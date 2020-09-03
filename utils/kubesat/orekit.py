"""
OreKit Utilities File
Wrapped Orekit Functions for Easy Use of Orbital Simulations
Function Summaries:
string_to_frame:                  allows creation of orekit frame objects from
								  set amount of strings
frame_to_string:                  converts orekit frame object to string that
								  works with string_to_frame function
t1_lte_t2_string:                 boolean comparison (time1 <= time2), time in ISO 8601 format
t1_gte_t2_string:                 boolean comparison (time1 >= time2), time in ISO 8601 format
absolute_time_converter_utc_manual:     turn time inputs into orekit absolute time object
absolute_time_converter_utc_string:     turn ISO 8601 string inputs into orekit absolute time object
convert_tle_string_to_TLE:        convert two tle line strings into orekit TLE object
TODO update references (prop1, prop2)
find_sat_distance:                distance between two propagators's at a given time
setup_orekit_zip_file:            sets up orekit with orekit-data.zip file (allows specification of zip file location)
keplerian_orbit:                  creates a keplerian orbit orekit object
visible_above_horizon:            returns whether a satellite is above the planet limb (horizon)
								  as viewed from another satellite in orbit at the specified time period
get_keplerian_parameters:         returns keplarian orbit parameters from orekit spacecraft state object


str_tle_propagator:               turns TLE string into orekit TLE propogator object
analytical_propagator:            returns EcksteinHechlerPropagator for a orekit orbit object
moving_body_pointing_law:         helper function for attitude_provider_constructor for pointing
                                  at a moving object that can be defined with a propagator

ground_pointing_law:              helper function for attitude_provider_constructor for pointing
                                  at an object on or very near earth's surface

nadir_pointing_law:               helper function for attitude_provider_constructor for pointing
								  at the nadir point (ground point directly below satellite)
attitude_provider_constructor:    with dictionary of inputs can return an altitude provider that
								  can be attached to a spacecraft object to define its pointing law
get_ground_passes:                provides times where satellite is visible overhead a certain point
								  on the earth (very useful for ground stations and IoT sensors)

check_iot_in_range:               very similar to get_ground_passes, but returns bool value for one
                                  time input
"""
import queue
import os
import queue
from enum import Enum
import numpy as np
from math import radians, pi, degrees

import orekit
from org.hipparchus.geometry.euclidean.threed import Vector3D
from orekit.pyhelpers import setup_orekit_curdir
from org.orekit.frames import FramesFactory, TopocentricFrame
from org.orekit.bodies import OneAxisEllipsoid, GeodeticPoint, CelestialBodyFactory
from org.orekit.time import TimeScalesFactory, AbsoluteDate, DateComponents, TimeComponents
from org.orekit.utils import IERSConventions, Constants, ElevationMask
from org.orekit.propagation.analytical.tle import TLE, TLEPropagator
from org.orekit.data import DataProvidersManager, ZipJarCrawler
from org.orekit.orbits import KeplerianOrbit, PositionAngle
from org.orekit.attitudes import CelestialBodyPointed, TargetPointing, NadirPointing
from org.orekit.propagation import SpacecraftState
from org.orekit.propagation.analytical import EcksteinHechlerPropagator, KeplerianPropagator
from org.orekit.propagation.events import EclipseDetector, EventsLogger, ElevationDetector, InterSatDirectViewDetector, FieldOfViewDetector
from org.orekit.propagation.events.handlers import ContinueOnEvent
from org.orekit.utils import IERSConventions
from org.orekit.propagation import SpacecraftState
from org.orekit.geometry.fov import CircularFieldOfView

from java.io import File

vm = orekit.initVM()
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
class utils(str, Enum):
	"""
	TODO: CLEAN UP....Enumeration for constants used in 
	"""
	ITRF = "ITRF"
	EME = "EME"
	TEME = "TEME"
	TOPOCENTRIC = "Topocentric"
	MOVING_BODY_TRACKING = "moving_body_tracking"
	GROUND_TRACKING = "ground_tracking"
	NADIR_TRACKING = "nadir_tracking"
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def field_of_view_detector(sat_propagator, latitude, longitude, altitude, start_time, degree_fov, duration=0, stepsize=1):
    """
    Determines if a ground point will be within the field of view (defined as a
    circular feild of view of however many degrees from the sat) for a specific
    sat_propagator that should include an integrated attitude provider.
    Args:
        sat_propagator: orekit propagator object that should include at the least
                        an internal orbit and attitude law (this law should either
                        be ground pointing or nadir pointing)
        latitude, longitude, altitude: (floats in degrees and meters) coordinate point
                                       to be checked if within feild of view of camera
        start_time: orekit absolute time object (start time of checking)
        degree_fov: (float in degrees) the full degree field of view of the camera/instrument
        duration: (int in seconds) duration to check after start time, if not inputed
                  will default to zero, and function will return a boolean for the
                  state at only the start time
        stepsize: (int >= 1) size in seconds between each prediction (smallest step is 1 second)
    Returns:
        duration=0:
            bool value that tells if the ground point is in the feild of view at the
            start time
        else:
            array of structure [[time_start, end_time], ... ,[start_end, end_time]] that
            contains the entry/exit times of the feild of view prediction.
    """
    earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
                         Constants.WGS84_EARTH_FLATTENING,
                         FramesFactory.getITRF(IERSConventions.IERS_2010, True))
    ground_target = GeodeticPoint(radians(float(latitude)),radians(float(longitude)), float(altitude))
    ground_target_frame = TopocentricFrame(earth, ground_target, "ground_target")
    circular_fov = CircularFieldOfView(Vector3D.PLUS_K, radians(float(degree_fov/2)),radians(0.))
    fov_detector = FieldOfViewDetector(ground_target_frame, circular_fov).withHandler(ContinueOnEvent())
    elevation_detector = ElevationDetector(ground_target_frame).withConstantElevation(0.0).withHandler(ContinueOnEvent())

    if (duration <= 0):
        return ((fov_detector.g(sat_propagator.propagate(start_time))<0) and (elevation_detector.g(sat_propagator.propagate(start_time))>0))

    time_within_fov = []
    time_array = [start_time.shiftedBy(float(time)) for time in np.arange(0, duration, stepsize)]
    entry_empty = True
    entry_time = 0
    for time in time_array:
        within_fov = ((fov_detector.g(sat_propagator.propagate(time))<0) and (elevation_detector.g(sat_propagator.propagate(time))>0))
        if (entry_empty and within_fov):
            entry_time = time
            entry_empty = False
        elif ((not entry_empty) and (not within_fov)):
            time_within_fov.append([entry_time,time])
            entry_empty = True
            entry_time = 0
        elif ((not entry_empty) and (time == time_array[-1])):
            time_within_fov.append([entry_time,time])

    return time_within_fov
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def string_to_frame(frame_name, latitude=0., longitude=0., altitude=0., name=""):
	"""
	Given a string with the following defined options below, the fucntion returns the orekit
	associated frame object.
	Args:
		frame_name: (string) with the following options...
					"ITRF" ... returns the ITRF (geocentric and rotates with earth for use
								for points near or on earth's surface--very accurate)
					"EME2000"/"J2000" ... Earth Centered Inertial (ECI) Frame
								  the frame is fixed to the celetial grid and doesn't rotate
								  with the earth
					"TEME" ... another ECI frame, but specifically used by NORAD TLEs
					"Topocentric" ... very specific frame defined at an coordinate on or near
									  the surface of an object (here we define earth). Rotates
									  with body defined by ITRF frame (can think as an offset
									  of ITRF frame for things like ground stations)
		latitude, longitude: (float in degrees) for defining the topocentric frame origin--not
							 required otherwise
		altitude: (float in meters) for defining the topocentric frame origin--not required otherwise
		name: (string) for defining the topocentric frame origin label--not required otherwise
	Returns:
		orekit frame object OR -1 if undefined string
	"""
	if (frame_name == utils.ITRF):
		return FramesFactory.getITRF(IERSConventions.IERS_2010, True)
	elif ((frame_name == utils.EME) or (frame_name == "J2000")):
		return FramesFactory.getEME2000()
	elif (frame_name == utils.TEME):
		return FramesFactory.getTEME()
	elif (frame_name == utils.TOPOCENTRIC):
		earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
						Constants.WGS84_EARTH_FLATTENING,
						FramesFactory.getITRF(IERSConventions.IERS_2010, True))
		location = GeodeticPoint(radians(latitude), radians(longitude), float(altitude))
		return TopocentricFrame(earth, location, name)
	else:
		return -1
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def frame_to_string(frame):
	"""
	Given a orekit frame object with the following defined options below, the fucntion returns the orekit
	associated frame string.
	Args:
		frame: (Frame) with the following options...
					ITRF (geocentric and rotates with earth for use
						for points near or on earth's surface--very accurate)
					Earth Centered Inertial (ECI) Frame
						the frame is fixed to the celetial grid and doesn't rotate
						with the earth
					ECI frame, but specifically used by NORAD TLEs
					very specific frame defined at an coordinate on or near
									  the surface of an object (here we define earth). Rotates
									  with body defined by ITRF frame (can think as an offset
									  of ITRF frame for things like ground stations)
	Returns:
		string OR -1 if undefined Frame
	"""
	if frame == FramesFactory.getITRF(IERSConventions.IERS_2010, True):
		return utils.ITRF
	elif frame == FramesFactory.getEME2000():
		return utils.EME
	elif frame== FramesFactory.getTEME():
		return utils.TEME
	else:
		return -1
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def visible_above_horizon(propagator_main_sat, propagator_tracked_sat, start_time, duration=0, stepsize=1, return_queue=False):
	"""
	Based on two propagators, determines if the main_sat can "see" another tracked_sat determinant on
	if the tracked_sat is above the planet limb (horizon) from the perspective of the main_sat, see
	different return options below.
	Args:
		propagator_main_sat, propagator_tracked_sat: any type of analytical propagator (ex. TLEPropagator)
		start_time: Orekit absolute time object (start time of tracking)
		duration: (int) seconds, how long Orekit will predict if visible. IF ZERO: ignores and
				  returns boolean cooresponding to start time
		stepsize: (int >= 1) size in seconds between each prediction (smallest step is 1 second)
		return_queue: (boolean) if True, changes return type to queue of durations since start time
					  that includes {start time, end time, start time, ...} as queue (for mapping)
	Returns: (Dependent on inputs...)
		bool: booleen value if duration is not entered, kept zero, or negative (this corresponds to if
		the tracked sat is visible at the start time)
		time_IsVisible: array of structure [[time_start, end_time], ... ,[start_end, end_time]] that
						contains the entry/exit times of the above horizon prediction.
						or
						if return_queue = True, then returns a queue of duration since start_time for
						these dates (for mapping function)
	"""
	#setup detector
	ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
	earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
						 Constants.WGS84_EARTH_FLATTENING,
						 ITRF)
	detector = InterSatDirectViewDetector(earth,propagator_tracked_sat).withHandler(ContinueOnEvent())
	#propogate for duration and create array of [time-stamp, bool] that tells if tracked_sat is visible to main_sat
	if (return_queue==True):
		time_IsVisible = queue.Queue(0)
	elif (duration > 0):
		time_IsVisible = []
	else:
		return(detector.g(propagator_main_sat.propagate(start_time)) > 0)
	time_array = [start_time.shiftedBy(float(time)) for time in np.arange(0, duration, stepsize)]
	entry_time = 0
	exit_time = 0
	for time in time_array:
		detector_value = detector.g(propagator_main_sat.propagate(time))
		#g here is the function that returns positive values if visible and negative if not visible
		if ((entry_time == 0) and (detector_value > 0)):
			entry_time = time
		elif ((entry_time != 0) and (detector_value <= 0) and (exit_time == 0)):
			exit_time = time
		elif ((entry_time != 0) and (exit_time != 0)):
			if (return_queue==True):
				time_IsVisible.put(exit_time.durationFrom(entry_time))
			else:
				time_IsVisible.append([entry_time,exit_time])
			entry_time = 0
			exit_time = 0
		elif ((entry_time != 0) and (exit_time == 0) and (time == time_array[-1])):
			if (return_queue==True):
				time_IsVisible.put(time.durationFrom(entry_time))
			else:
				time_IsVisible.append([entry_time,time])
	return time_IsVisible
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def setup_orekit_zip_file(filename=' '):
	"""
	This function attempts to load the orekit-data.zip from 5 places: the user's home directory
	the root directory, where the user specified + the "orekit-data.zip", where the user
	specified, and in the directory the function was called from.
	If successful, it sets up the Orekit DataProviders to access it and sets up the java
	engine with orekit.
	note -- Java VM needs to be initiated prior to calling this function with
			orekit.initVM()
	Inputs: filename (str): Path of zip with orekit data
	Outputs: Boolean true if successful
	"""
	prospective_files = []

	# Try the user's home directory
	home = os.path.expanduser("~")
	path = os.path.join(home, 'orekit-data.zip')
	prospective_files.append(File(path))
	prospective_files[0] = File(prospective_files[0].absolutePath)

	# Try in the root directory

	root = ('/orekit-data.zip')
	prospective_files.append(File(path))
	prospective_files[1] = File(prospective_files[1].absolutePath)

	# Try with the user's path + '/orekit-data.zip'

	path = os.path.join(filename, 'orekit-data.zip')
	prospective_files.append(File(path))
	prospective_files[2] = File(prospective_files[2].absolutePath)

	# Try what the user actually entered

	prospective_files.append(File(path))
	prospective_files[3] = File(prospective_files[3].absolutePath)

	# Try 'orekit-data.zip' in the current directory

	path = 'orekit-data.zip'
	prospective_files.append(File(path))
	prospective_files[4] = File(prospective_files[4].absolutePath)


	datafile = prospective_files[0] #initialize datafile

	if prospective_files[1].exists():
		datafile = prospective_files[1]

	elif prospective_files[2].exists():
		datafile = prospective_files[2]

	elif prospective_files[3].exists():
		datafile = prospective_files[3]

	elif prospective_files[4].exists():
		datafile = prospective_files[4]

	if not datafile.exists():
		print('File not found in:', prospective_files[1].absolutePath, '\n',
			 prospective_files[2].absolutePath, '\n',
			 prospective_files[3].absolutePath, '\n',
			 prospective_files[4].absolutePath, '\n')
		print("""
		The Orekit library relies on some external data for physical models.
		Typical data are the Earth Orientation Parameters and the leap seconds history,
		both being provided by the IERS or the planetary ephemerides provided by JPL.
		Such data is stored in text or binary files with specific formats that Orekit knows
		how to read, and needs to be provided for the library to work.
		You can download a starting file with this data from the orekit gitlab at:
		https://gitlab.orekit.org/orekit/orekit-data
		or by the function:
		orekit.pyhelpers.download_orekit_data_curdir()
		""")
		return False

	DM = DataProvidersManager.getInstance()
	crawler = ZipJarCrawler(datafile)
	DM.clearProviders()
	DM.addProvider(crawler)
	return True
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def t1_gte_t2_string(time1, time2):
	"""
	Returns true of time1 comes after or is equal to time2
	Args:
		time1 (string): time1 in ISO-8601 standard
		time2 (string): time2 in ISO-8601 standard
		Ex. '2020-12-03T00:00:00.000'
	Returns:
		boolean: true if time1 comes after or is equal to time2
	"""
	return absolute_time_converter_utc_string(time1).isAfterOrEqualTo(absolute_time_converter_utc_string(time2))
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def t1_lte_t2_string(time1, time2):
	"""
	Inputs: time1, time2 (two strings)
	Output: booleen value (true if time1 less than or equal to time2)
	"""
	return absolute_time_converter_utc_string(time1).isBeforeOrEqualTo(absolute_time_converter_utc_string(time2))
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def absolute_time_converter_utc_manual(year, month, day, hour=0, minute=0, second=0.0):
	"""
	turn time into orekit absolute time object
	Inputs: time scales in UTC
	Output: absolute time object from orekit
	"""
	return AbsoluteDate(int(year), int(month), int(day), int(hour), int(minute), float(second), TimeScalesFactory.getUTC())
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def absolute_time_converter_utc_string(time_string):
	"""
	turn time_string into orekit absolute time object
	Inputs: time scales in UTC
	Output: absolute time object from orekit
	"""
	return AbsoluteDate(time_string, TimeScalesFactory.getUTC())
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def convert_tle_string_to_TLE(tle_line1, tle_line2):
	"""
	convert two tle line strings into orekit TLE object
	Inputs: tle_line1, tle_line2 (tle two line element strings)
		Ex: tle_line1 = "1 25544U 98067A   20174.66385417  .00000447  00000-0  16048-4 0  9992"
			tle_line2 = "2 25544  51.6446 321.3575 0002606  75.8243 105.9183 15.49453790232862"
	Output: Orekit TLE object
	"""
	return TLE(tle_line1,tle_line2)
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def find_sat_distance(prop1, prop2, time):
	"""
	distance between two propagators at a given time
	Inputs: prop1/prop2 (Two orekit propagator objects), time (orekit absolute time object--utc)
	Output: Distance (meters)
	"""
	ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
	earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS, Constants.WGS84_EARTH_FLATTENING, ITRF)

	pv_1 = prop1.getPVCoordinates(time, prop1.getFrame())
	pv_2 = prop2.getPVCoordinates(time, prop2.getFrame())

	p_1 = pv_1.getPosition()
	p_2 = pv_2.getPosition()

	return abs(Vector3D.distance(p_1, p_2))
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def check_sats_in_range(callback_function):
	"""
	DO NOT DELETE -- FOR NATS MESSAGING
	"""
	return callback_function
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def keplerian_orbit(parameters):
    """
	Given a dictionary of parameters containg eccentricity, semimajor_axis, inclination, perigee_argument, right
	acension of ascending node, anomaly, anomaly_type and orbit_update_date this function returns a keplerian
	orbit orekit object
	Args:
		parameters (dict): dictionary of parameters containg eccentricity, semimajor_axis (meters),
        inclination, perigee argument, right ascension of ascending node, orbit_update_date,
        and anomoly with another defining key
        ["anomaly_type"] = "MEAN" or "TRUE"
        ["frame"] = "EME2000", "J2000", or "TEME" only
    Ex.
            parameters = {
                        "eccentricity": 0.0008641,
                        "semimajor_axis": 6801395.04,
                        "inclination": radians(87.0),
                        "perigee_argument": radians(20.0),
                        "right_ascension_of_ascending_node":radians(10.0),
                        "anomaly": radians(0.0),
                        "anomaly_type": "TRUE",
                        "orbit_update_date":'2021-12-02T00:00:00.000',
                        "frame": "EME"}
	Returns:
		KeplerianOrbit: Keplerian orbit orekit object
	"""
    eccentricity = float(parameters["eccentricity"])
    semimajor_axis = float(parameters["semimajor_axis"])
    inclination = float(parameters["inclination"])
    perigee_argument = float(parameters["perigee_argument"])
    right_ascension_of_ascending_node = float(parameters["right_ascension_of_ascending_node"])
    anomaly = float(parameters["anomaly"])
    orbit_update_date = absolute_time_converter_utc_string(parameters["orbit_update_date"])
    frame = string_to_frame(parameters["frame"])

    if (parameters["anomaly_type"] == "TRUE"):
        return KeplerianOrbit(semimajor_axis, eccentricity, inclination, perigee_argument, right_ascension_of_ascending_node,
        anomaly, PositionAngle.TRUE, frame, orbit_update_date, Constants.WGS84_EARTH_MU)
    elif (parameters["anomaly_type"] == "MEAN"):
        return KeplerianOrbit(semimajor_axis, eccentricity, inclination, perigee_argument, right_ascension_of_ascending_node,
        anomaly, PositionAngle.MEAN, frame, orbit_update_date, Constants.WGS84_EARTH_MU)
    else:
        return("Error: Need to redefine anomoly_type, see function documentation")
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def get_keplerian_parameters(spacecraft_state, anomaly_type = "TRUE"):
    """
	Given a SpaceCraftState object this function computes the keplerian orbit parameters
    Note: parameter values may change but they'll define the same orbit
	Args:
		spacecraft_state (SpaceCraftState): SpaceCraftState orekit object that has an orbit attribute
        anomaly_type (string; "MEAN" or "TRUE"): tells to return true or mean anomaly, defaults to TRUE
	Returns:
		dict: dictionary of parameters containg eccentricity, semimajor_axis, inclination, perigee argument, right
		ascension of ascending node, anomaly, anomaly_type, and orbit_update_date
    """
    parameters = dict()
    new_orbit = KeplerianOrbit(spacecraft_state.getOrbit())

    parameters["semimajor_axis"] = new_orbit.getA()
    parameters["eccentricity"] = new_orbit.getE()
    parameters["inclination"] = new_orbit.getI()
    parameters["perigee_argument"] = new_orbit.getPerigeeArgument()
    parameters["right_ascension_of_ascending_node"] = new_orbit.getRightAscensionOfAscendingNode()
    parameters["orbit_update_date"] = new_orbit.getDate().toString()
    parameters["frame"] = frame_to_string(spacecraft_state.getFrame())
    if (anomaly_type == "MEAN"):
        parameters["anomaly"] = new_orbit.getMeanAnomaly()
        parameters["anomaly_type"] = "MEAN"
    else:
        parameters["anomaly"] = new_orbit.getTrueAnomaly()
        parameters["anomaly_type"] = "TRUE"
    return parameters

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def str_tle_propagator(tle_1, tle_2):
	"""
	Creates propogator for string format TLE
	Args:
		tle_1, tle_2 (strings) line 1 and line 2 of a NORAD TLE
	Returns:
		TLEPropagator orekit object
	"""
	return TLEPropagator.selectExtrapolator(convert_tle_string_to_TLE(tle_1, tle_2))
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def analytical_propagator(parameters):
	"""
	Takes in a dictionary of keplarian parameters and returns an Keplarian analytical propogator
	Args:
		Args:
    		parameters (dict): dictionary of parameters containg eccentricity, semimajor_axis (meters),
            inclination, perigee argument, right ascension of ascending node, orbit_update_date, and
            anomoly with another defining key
            ["anomaly_type"] = "MEAN" or "TRUE"
            ["frame"] = "EME2000", "J2000", or "TEME" only
        Ex.
                parameters = {
                            "eccentricity": 0.0008641,
                            "semimajor_axis": 6801395.04,
                            "inclination": radians(87.0),
                            "perigee_argument": radians(20.0),
                            "right_ascension_of_ascending_node":radians(10.0),
                            "anomaly": radians(0.0),
                            "anomaly_type": "TRUE",
                            "orbit_update_date":'2021-12-02T00:00:00.000',
                            "frame": "EME"}
	Returns:
		AbstractAnalyticalPropagator: propagator that can be used to propagate an orbit
                                      and acts as a PVCoordinatesProvider
                                      (PV = position, velocity)
	"""
	return KeplerianPropagator(keplerian_orbit(parameters), Constants.WGS84_EARTH_MU)
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def moving_body_pointing_law(orbit_to_track_propagator, parameters):
	"""Takes in the propagator of a satellite and returns a attitude law or attituded provider to track that satellite
	Args:
		orbit_to_track_propagator: (AbstractAnalyticalPropagator or PVCoordinateProvider)
                                   propagator for the orbit desired to be tracked
        parameters: dictionary containing at least...
                    parameters["frame"] = "EME2000", "J2000", or "TEME" only
	Returns:
		AttitudeProvider: AttitudeLaw that can be added to a propagator in order to simulate tracking
	"""
	frame = string_to_frame(parameters["frame"])
	return CelestialBodyPointed(frame, orbit_to_track_propagator,
									Vector3D.PLUS_K, Vector3D.PLUS_K, Vector3D.MINUS_J)
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def ground_pointing_law(parameters):
	"""
	Given a longitude, lattitude, and altitude it returns a ground pointing attitude law
	Args:
		parameters: dictionary containing at least...
                    parameters["frame"] = (str) "EME2000", "J2000", or "TEME" only
                    parameters["latitude"] = (float -- radians) latitude
                    parameters["longitude"] = (float -- radians) longitude
                    parameters["altitude"] = (float -- meters) altitude above sea level
	Returns:
		AttidueProvider: attitude law that tells the satellite to point at a specific point on the ground
	"""
	ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
	earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
							 Constants.WGS84_EARTH_FLATTENING,
							 ITRF)
	point = GeodeticPoint(float(parameters["latitude"]), float(parameters["longitude"]), float(parameters["altitude"]))
	frame = string_to_frame(parameters["frame"])
	return TargetPointing(frame, point, earth)
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def nadir_pointing_law(parameters):
    """
    Returns a nadir pointing attitude law (points to ground point directly below) for the earth as the
    celestial body orbited
    Args:
        parameters: dictionary containing at least...
                    parameters["frame"] = (str) "EME", "J2000", or "TEME" only
    Returns:
        AttidueProvider: attitude law that tells the satellite to point at nadir
    """
    ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
    earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
                             Constants.WGS84_EARTH_FLATTENING,
                             ITRF)
    frame = string_to_frame(parameters["frame"])
    return NadirPointing(frame, earth)
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def attitude_provider_constructor(attitude_provider_type, parameters):
	"""
	Takes in an attitude provider type and the parameters necessary for that type
    to return a desired attitude law provider...
	Args:
    Dependent on the attitude_provider_type, the accompaning parameters dictionary
    should contain different information for the pointing...

    attitude_provider_type (string): the name of pointing law
                                     "moving_body_tracking", "ground_tracking",
                                     or "nadir_tracking"
    parameters (dict): values dependent on attitude_provider_type
        "moving_body_tracking":
            parameters contains eccentricity, semimajor_axis (meters), inclination,
            perigee argument, right ascension of ascending node, orbit_update_date,
            and anomoly with another defining key
                ["anomaly_type"] = "MEAN" or "TRUE"
                ["frame"] = "EME2000", "J2000", or "TEME" only
            ALL OF THESE DESCRIBE THE ORBIT OF THE SAT BEING TRACKED, NOT THE
            TRACKING SAT
            ex.
            parameters = {
                        "eccentricity": 0.0008641,
                        "semimajor_axis": 6801395.04,
                        "inclination": radians(87.0),
                        "perigee_argument": radians(20.0),
                        "right_ascension_of_ascending_node":radians(10.0),
                        "anomaly": radians(0.0),
                        "anomaly_type": "TRUE",
                        "orbit_update_date":'2021-12-02T00:00:00.000',
                        "frame": "EME"}
        "ground_tracking":
            parameters should be a dictonary containing the frame (of the tracking
            satellite), lattitude, longitude, and altitude of the location with
            respect to the earth (see ground_pointing_law for more documentation)
        "nadir_tracking":
            parameters should be a dictonary containing the frame of the tracking
            satellite (parameters['frame'])
            ["frame"] = "EME2000", "J2000", or "TEME" only

	Returns:
		AttitudeProvider: Attitude provider of specified pointing law, can be added
        to propagator to define satellite's pointing
	"""
	if attitude_provider_type == utils.MOVING_BODY_TRACKING:

		orbit_to_track_propagator = analytical_propagator(parameters)

		return moving_body_pointing_law(orbit_to_track_propagator, parameters)

	elif attitude_provider_type  == utils.GROUND_TRACKING:
		return ground_pointing_law(parameters)

	elif attitude_provider_type  == utils.NADIR_TRACKING:
		return nadir_pointing_law(parameters)
	else:
		return "Attitude Law type unknown"
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def get_ground_passes(propagator, grstn_latitude, grstn_longitude, grstn_altitude, start, stop, ploting_param=False):
	"""
	Gets all passes for a specific satellite occuring during the given range. Pass is defined as 10° above the horizon,
	below this is unusable (for our purposes)
	Args:
		propagator ([any] OreKit orbit propagator): propagator, TLEPropagator or KeplerianPropagator for the
													satellite in question
		grstn_latitude (Float): latitude of the ground station in degrees
		grstn_longitude (Float): longitude of the ground station in degrees
		start (OreKit AbsoluteDate): the beginning of the desired time interval
		stop (OreKit AbsoluteDate): the end of the desired time interval
		plotting_param (Boolean): do not use, used by potential plotter
	Return value:
		A dictionary with {"start":[OreKit AbsoluteDate], "stop":[OreKit AbsoluteDate], "duration": (seconds) [float]}
		Alternatively, returns a queue of times in reference to the start time for ease of plotting ground passes.
	Notes:
		use absolutedate_to_datetime() to convert from AbsoluteDate
	TODO: add ElevationMask around ground station to deal with topography blocking communications
	"""

	ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
	earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
						 Constants.WGS84_EARTH_FLATTENING,
						 ITRF)

	gs_location = GeodeticPoint(radians(grstn_latitude), radians(grstn_longitude), float(grstn_altitude))
	gs_frame = TopocentricFrame(earth, gs_location, "ground station")

	elevation_detector = ElevationDetector(gs_frame).withConstantElevation(0.0).withHandler(ContinueOnEvent())
	logger = EventsLogger()
	logged_detector = logger.monitorDetector(elevation_detector)

	propagator.addEventDetector(logged_detector)
	state = propagator.propagate(start, stop)

	events = logger.getLoggedEvents()
	pass_start_time = None
	result = []
	if not ploting_param:
		for event in logger.getLoggedEvents():
			if event.isIncreasing():
				pass_start_time = event.getState().getDate()
			else:
				stop_time = event.getState().getDate()
				result.append({"start": pass_start_time,
							   "stop": stop_time,
							   "duration": stop_time.durationFrom(start)/60})
				pass_start_time = None
	else:
		result = queue.Queue(0)
		for event in logger.getLoggedEvents():
			if event.isIncreasing():
				pass_start_time = event.getState().getDate()
			else:
				pass_stop_time = event.getState().getDate()
				result.put(pass_start_time.durationFrom(start)) # start is the initial time of interest
				result.put(pass_stop_time.durationFrom(start))
				pass_start_time = None

	return result
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def check_iot_in_range(propagator, grstn_latitude, grstn_longitude, grstn_altitude, time):
	"""
	Determines whether a satellite is above the horizon at a specific time
	in the reference frame of a ground station
	Args:
        propagator: orekit propagator object of overhead satellite
		grstn_latitude (float): (degrees) groudn station latitude
		grstn_longitude (float): (degrees) ground station longitude
		grstn_altitude (float): (meters) ground station altitude
		time (string): time at which the range check is to occur.
	"""
	ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
	earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
						 Constants.WGS84_EARTH_FLATTENING,
						 ITRF)

	gs_location = GeodeticPoint(radians(grstn_latitude), radians(grstn_longitude), float(grstn_altitude))
	gs_frame = TopocentricFrame(earth, gs_location, "ground station")
	pv = propagator.getPVCoordinates(time, propagator.getFrame())
	elevation = degrees(gs_frame.getElevation(pv.getPosition(),
					propagator.getFrame(),time))

	if elevation > 0:
		return True

	return False
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
setup_orekit_zip_file()

"""
Tests for the OreKit utility functions in orekit_utils.py
"""
import asyncio
import unittest
from unittest import TestCase, IsolatedAsyncioTestCase
from time import sleep
import sys
sys.path.append('../../')
import os
from math import radians
import orekit
from org.hipparchus.geometry.euclidean.threed import Vector3D
from org.orekit.time import TimeScalesFactory, AbsoluteDate, DateComponents, TimeComponents
from org.orekit.propagation.analytical import KeplerianPropagator, EcksteinHechlerPropagator
from org.orekit.attitudes import CelestialBodyPointed, TargetPointing
from org.orekit.utils import Constants
from org.orekit.propagation.analytical.tle import TLE, TLEPropagator
from org.orekit.orbits import KeplerianOrbit, PositionAngle
from org.orekit.frames import FramesFactory, TopocentricFrame
from org.orekit.utils import IERSConventions
from org.orekit.bodies import OneAxisEllipsoid, GeodeticPoint, CelestialBodyFactory
from org.orekit.propagation import SpacecraftState
import kubesat.orekit as orekit_utils
from kubesat.orekit import get_ground_passes, check_iot_in_range, setup_orekit_zip_file
from kubesat.orekit import t1_gte_t2_string, t1_lte_t2_string, keplerian_orbit, analytical_propagator, analytical_propagator, moving_body_pointing_law, ground_pointing_law, attitude_provider_constructor, absolute_time_converter_utc_string, analytical_propagator, ground_pointing_law

vm = orekit.initVM()
setup_orekit_zip_file(' ')

class Tests(TestCase):
    """
    Testing OreKit utilities
    """

    def test_string_to_frame(self):
        """
        string_to_frame tests
        """
        frame_ITRF_1 = orekit_utils.string_to_frame("ITRF")
        frame_ITRF_2 = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
        self.assertTrue(frame_ITRF_1.equals(frame_ITRF_2))

        frame_EME2000_1 = orekit_utils.string_to_frame("EME")
        frame_EME2000_2 = FramesFactory.getEME2000()
        frame_EME2000_3 = orekit_utils.string_to_frame("J2000")
        self.assertTrue(frame_EME2000_1.equals(frame_EME2000_2) and
                            frame_EME2000_1.equals(frame_EME2000_3))

        frame_TEME_1 = orekit_utils.string_to_frame("TEME")
        frame_TEME_2 = FramesFactory.getTEME()
        self.assertTrue(frame_TEME_1.equals(frame_TEME_2))


        frame_Topo_1 = orekit_utils.string_to_frame("Topocentric", 5., 5., 5., "groundstation_1")
        earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
                         Constants.WGS84_EARTH_FLATTENING,
                         FramesFactory.getITRF(IERSConventions.IERS_2010, True))
        location = GeodeticPoint(radians(5.), radians(5.), 5.)
        frame_Topo_2 = TopocentricFrame(earth, location, "groundstation_1")
        self.assertTrue(frame_Topo_1.getNadir().equals(frame_Topo_2.getNadir()))

    def test_nadir_pointing_law(self):
        """
        nadir_pointing_law tests (will throw error if doesn't work), no direct assert tests here
        """
        parameters = {"frame": "TEME"}
        attitudeProvider = orekit_utils.nadir_pointing_law(parameters)
        tle = TLE("1 44235U 19029A   20178.66667824  .02170155  00000-0  40488-1 0  9998",
                    "2 44235  00.0000 163.9509 0005249 306.3756  83.0170 15.45172567 61683")
        propagator = TLEPropagator.selectExtrapolator(tle, attitudeProvider, 4.)

    def test_field_of_view_detector(self):
        """
        field_of_view_detector tests
        """
        tle = TLE("1 44235U 19029A   20178.66667824  .02170155  00000-0  40488-1 0  9998",
                    "2 44235  00.0000 163.9509 0005249 306.3756  83.0170 15.45172567 61683")
        parameters = {"frame": "TEME"}
        attitudeProvider = orekit_utils.nadir_pointing_law(parameters)
        propogator_fov = TLEPropagator.selectExtrapolator(tle, attitudeProvider, 4.)
        startDate = AbsoluteDate(2020, 6, 26, 1, 40, 00.000, TimeScalesFactory.getUTC())
        #should have one passes
        self.assertTrue(len(orekit_utils.field_of_view_detector(propogator_fov, 0, 0, 0, startDate, 20, 5400))==1)
        #should have zero passes
        self.assertTrue(len(orekit_utils.field_of_view_detector(propogator_fov, 0, 0, 0, startDate, 20, 100))==0)
        #test exact time input
        self.assertFalse(orekit_utils.field_of_view_detector(propogator_fov, 0, 0, 0, startDate, 20))

    def test_setup_orekit_zip_file(self):
        """
        Testing setup of OreKit
        """
        vm = orekit.initVM()
        assert setup_orekit_zip_file(' ')

    def test_absolute_time_converter_utc_manual(self):
        """
        absolute_time_converter_utc_manual tests
        """
        self.assertEqual(orekit_utils.absolute_time_converter_utc_manual(2020,12,2).toString(), '2020-12-02T00:00:00.000')
        self.assertEqual(orekit_utils.absolute_time_converter_utc_manual(2020,12,2,3).toString(), '2020-12-02T03:00:00.000')
        self.assertEqual(orekit_utils.absolute_time_converter_utc_manual(2020,12,2,3,12).toString(), '2020-12-02T03:12:00.000')
        self.assertEqual(orekit_utils.absolute_time_converter_utc_manual(2020,12,2,3,12,13).toString(), '2020-12-02T03:12:13.000')
        self.assertEqual(orekit_utils.absolute_time_converter_utc_manual(2020,12,2,3,12,13.2).toString(), '2020-12-02T03:12:13.200')

    def test_absolute_time_converter_utc_string(self):
        """
        absolute_time_converter_utc_string tests
        """
        self.assertTrue(orekit_utils.absolute_time_converter_utc_manual(2020,12,2).isEqualTo(orekit_utils.absolute_time_converter_utc_string('2020-12-02T00:00:00.000')))
        self.assertTrue(orekit_utils.absolute_time_converter_utc_manual(2020,12,2,3).isEqualTo(orekit_utils.absolute_time_converter_utc_string('2020-12-02T03:00:00.000')))
        self.assertTrue(orekit_utils.absolute_time_converter_utc_manual(2020,12,2,3,12).isEqualTo(orekit_utils.absolute_time_converter_utc_string('2020-12-02T03:12:00.000')))
        self.assertTrue(orekit_utils.absolute_time_converter_utc_manual(2020,12,2,3,12,13).isEqualTo(orekit_utils.absolute_time_converter_utc_string('2020-12-02T03:12:13.000')))
        self.assertTrue(orekit_utils.absolute_time_converter_utc_manual(2020,12,2,3,12,13.2).isEqualTo(orekit_utils.absolute_time_converter_utc_string('2020-12-02T03:12:13.200')))

    def test_t1_gte_t2_string(self):
        """
        t1_gte_t2_string tests
        """
        self.assertTrue(orekit_utils.t1_gte_t2_string('2020-12-03T00:00:00.000','2020-12-02T00:00:00.000'))
        self.assertTrue(orekit_utils.t1_gte_t2_string('2020-12-03T00:00:00.000','2020-12-03T00:00:00.0'))

    def test_t1_lte_t2_string(self):
        """
        t1_lte_t2_string tests
        """
        self.assertFalse(orekit_utils.t1_lte_t2_string('2020-12-03T00:00:00.000','2020-12-02T00:00:00.000'))
        self.assertTrue(orekit_utils.t1_lte_t2_string('2020-12-03T00:00:00.000','2020-12-03T00:00:00.0'))

    def test_convert_tle_string_to_TLE(self):
        """
        convert_tle_string_to_TLE tests
        """
        tle_line1 = "1 25544U 98067A   20174.66385417  .00000447  00000-0  16048-4 0  9992"
        tle_line2 = "2 25544  51.6446 321.3575 0002606  75.8243 105.9183 15.49453790232862"
        tle2_line1 = "1 44235U 19029A   20178.58335648  .01685877  00000-0  31131-1 0  9991"
        tle2_line2 = "2 44235  52.9995 164.3403 0009519 291.6111 354.0622 15.45232749 61668"
        self.assertTrue(orekit_utils.convert_tle_string_to_TLE(tle_line1, tle_line2).equals(orekit_utils.convert_tle_string_to_TLE(tle_line1, tle_line2)))
        self.assertFalse(orekit_utils.convert_tle_string_to_TLE(tle_line1, tle_line2).equals(orekit_utils.convert_tle_string_to_TLE(tle2_line1, tle2_line2)))
        self.assertEqual(orekit_utils.convert_tle_string_to_TLE(tle_line1, tle_line2).getLine2(),tle_line2)

    def test_str_tle_propagator(self):
        tle_line1 = "1 25544U 98067A   20174.66385417  .00000447  00000-0  16048-4 0  9992"
        tle_line2 = "2 25544  51.6446 321.3575 0002606  75.8243 105.9183 15.49453790232862"
        propagator_1 = orekit_utils.str_tle_propagator(tle_line1, tle_line2)
        TLE = orekit_utils.convert_tle_string_to_TLE(tle_line1, tle_line2)
        propagator_2 = TLEPropagator.selectExtrapolator(TLE)
        time = absolute_time_converter_utc_string('2020-12-02T00:00:00.000')
        self.assertTrue(propagator_1.propagate(time).getOrbit().toString() == propagator_2.propagate(time).getOrbit().toString())

    def test_find_sat_distance(self):
        """
        find_distance tests: test some well known distances and zero cases
        """
        tle_line1 = "1 25544U 98067A   20174.66385417  .00000447  00000-0  16048-4 0  9992"
        tle_line2 = "2 25544  51.6446 321.3575 0002606  75.8243 105.9183 15.49453790232862"
        tle2_line1 = "1 44235U 19029A   20178.58335648  .01685877  00000-0  31131-1 0  9991"
        tle2_line2 = "2 44235  52.9995 164.3403 0009519 291.6111 354.0622 15.45232749 61668"

        prop1 = orekit_utils.str_tle_propagator(tle_line1, tle_line2)
        prop2 = orekit_utils.str_tle_propagator(tle2_line1, tle2_line2)

        time = orekit_utils.absolute_time_converter_utc_string('2020-12-02T00:00:00.000')

        self.assertEqual(orekit_utils.find_sat_distance(prop1,prop2,time),orekit_utils.find_sat_distance(prop1,prop2,time))
        self.assertEqual(orekit_utils.find_sat_distance(prop1,prop1,time),0.)
        self.assertEqual(orekit_utils.find_sat_distance(prop2,prop2,time),0.)

    def test_get_ground_passes(self):
        """
        Testing whether OreKit finds ground passess
        """
        # test will fail if setup_orekit fails

        utc = TimeScalesFactory.getUTC()
        ra = 500 * 1000         #  Apogee
        rp = 400 * 1000         #  Perigee
        i = radians(55.0)      # inclination
        omega = radians(20.0)   # perigee argument
        raan = radians(10.0)  # right ascension of ascending node
        lv = radians(0.0)    # True anomaly

        epochDate = AbsoluteDate(2020, 1, 1, 0, 0, 00.000, utc)
        initial_date = epochDate

        a = (rp + ra + 2 * Constants.WGS84_EARTH_EQUATORIAL_RADIUS) / 2.0
        e = 1.0 - (rp + Constants.WGS84_EARTH_EQUATORIAL_RADIUS) / a

        ## Inertial frame where the satellite is defined
        inertialFrame = FramesFactory.getEME2000()

        ## Orbit construction as Keplerian
        initialOrbit = KeplerianOrbit(a, e, i, omega, raan, lv,
                                    PositionAngle.TRUE,
                                    inertialFrame, epochDate, Constants.WGS84_EARTH_MU)

        propagator = KeplerianPropagator(initialOrbit)
        durand_lat = 37.4269
        durand_lat = -122.1733
        durand_alt = 10.0

        output = get_ground_passes(propagator, durand_lat, durand_lat, durand_alt, initial_date, initial_date.shiftedBy(3600.0 * 24), ploting_param=False)
        assert len(output) == 5

    def test_check_iot_in_range(self):
        """
        check_iot_in_range test
        """
        tle_line1 = "1 44235U 19029A   20178.66667824  .02170155  00000-0  40488-1 0  9998"
        tle_line2 = "2 44235  00.0000 163.9509 0005249 306.3756  270.0170 15.45172567 61683"
        prop1 = orekit_utils.str_tle_propagator(tle_line1, tle_line2)
        lat = 0.
        lon = 0.
        alt = 10.
        time = AbsoluteDate(2020, 6, 26, 1, 40, 00.000, TimeScalesFactory.getUTC())
        self.assertTrue(check_iot_in_range(prop1, lat, lon, alt, time))
        self.assertFalse(check_iot_in_range(prop1, lat, lon, alt, time.shiftedBy(60.*30.)))

    def test_t1_gte_t2_string(self):
        """
        t1_gte_t2_string test
        """
        self.assertTrue(t1_gte_t2_string("2021-12-02T00:00:00.000","2021-12-01T00:00:00.000"))
        self.assertTrue(t1_gte_t2_string("2021-12-02T00:00:00.500","2021-12-01T00:00:00.000"))
        self.assertTrue(t1_gte_t2_string("2021-12-02T00:05","2021-12-01T00:00"))
        self.assertTrue(t1_gte_t2_string("2021-12-02T00:00:00.5","2019-12-01T12:00:00.000"))
        self.assertFalse(t1_gte_t2_string("2021-12-02T00:00:00.5","2035-12-01T14:00:00.000"))


    def test_t1_lte_t2_string(self):
        """
        t1_lte_t2_string test
        """
        self.assertTrue(t1_lte_t2_string('2005-12-02T00:00:00.000','2021-12-01T00:00:00.000'))
        self.assertFalse(t1_lte_t2_string('2021-12-02T00:00:00.000','2021-12-01T00:55:00.555'))
        self.assertFalse(t1_lte_t2_string('2021-12-02T00:00:00.500','2019-12-01T12:00:00.000'))
        self.assertTrue(t1_lte_t2_string('2021-12-02T00:00:00.5','2035-12-01T12:00:00.000'))

    def test_frame_to_string(self):
        """
        frame_to_string test
        """
        EME = FramesFactory.getEME2000()
        ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
        TEME = FramesFactory.getTEME()
        self.assertTrue(orekit_utils.frame_to_string(EME) == "EME")
        self.assertTrue(orekit_utils.frame_to_string(ITRF) == "ITRF")
        self.assertTrue(orekit_utils.frame_to_string(TEME) == "TEME")

    def test_keplerian_orbit(self):
        """
        keplerian_orbit test
        """
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
        k_orbit = keplerian_orbit(parameters)

        eccentricity = parameters["eccentricity"]
        semimajor_axis = parameters["semimajor_axis"]
        inclination = parameters["inclination"]
        perigee_argument = parameters["perigee_argument"]
        right_ascension_of_ascending_node = parameters["right_ascension_of_ascending_node"]
        true_anomaly = parameters["anomaly"]
        orbit_update_date = parameters["orbit_update_date"]
        epochDate = absolute_time_converter_utc_string(orbit_update_date)
        frame = orekit_utils.string_to_frame(parameters["frame"])

        self.assertTrue(KeplerianOrbit(semimajor_axis, eccentricity, inclination, perigee_argument,
                                    right_ascension_of_ascending_node,
                                    true_anomaly, PositionAngle.TRUE,
                                    frame, epochDate,
                                    Constants.WGS84_EARTH_MU).toString() == k_orbit.toString())
    def test_get_keplerian_parameters(self):
        """
        get_keplerian_parameters test
        """
        parameters = {
                    "eccentricity": 0.0008641,
                    "semimajor_axis": 6801395.04,
                    "inclination": radians(87.0),
                    "perigee_argument": radians(20.0),
                    "right_ascension_of_ascending_node": radians(10.0),
                    "anomaly": radians(0.0),
                    "anomaly_type": "TRUE",
                    "orbit_update_date":'2021-12-02T00:00:00.000',
                    "frame": "EME"}

        propagator_1 = analytical_propagator(parameters)
        orbit = keplerian_orbit(parameters)

        new_state = SpacecraftState(orbit)
        new_parameters = orekit_utils.get_keplerian_parameters(new_state)

        propagator_2 = keplerian_orbit(new_parameters)
        new_time = absolute_time_converter_utc_string('2021-12-05T00:00:00.000')

        distance = orekit_utils.find_sat_distance(propagator_1, propagator_2, new_time)
        # parameters value change but define same orbit
        self.assertTrue(distance <= 0.000001)

    def test_visible_above_horizon(self):
        """
        visible_above_horizon test
        """
        #equitorial orbit
        tle_line1 = "1 44235U 19029A   20178.66667824  .02170155  00000-0  40488-1 0  9998"
        tle_line2 = "2 44235  00.0000 163.9509 0005249 306.3756  83.0170 15.45172567 61683"
        #high inclination orbit
        tle2_line1 = "1 44235U 19029A   20178.66667824  .02170155  00000-0  40488-1 0  9998"
        tle2_line2 = "2 44235  70.0000 163.9509 0005249 306.3756  83.0170 15.45172567 61683"
        prop1 = orekit_utils.str_tle_propagator(tle_line1, tle_line2)
        prop2 = orekit_utils.str_tle_propagator(tle2_line1, tle2_line2)
        time = AbsoluteDate(2020, 6, 26, 1, 40, 00.000, TimeScalesFactory.getUTC())

        #verified with graphing overviews
        self.assertFalse(orekit_utils.visible_above_horizon(prop1, prop2, time))
        self.assertTrue(orekit_utils.visible_above_horizon(prop1, prop2, time.shiftedBy(60.*10.)))
        self.assertTrue(orekit_utils.visible_above_horizon(prop1, prop2, time.shiftedBy(60.*10. + 45.*60.)))
        time_period_visible = orekit_utils.visible_above_horizon(prop1, prop2, time, 60*30)[0]
        self.assertTrue(time.shiftedBy(60.*10.).isBetween(time_period_visible[0],time_period_visible[1]))


    def test_analytical_propagator(self):
        """
        analytical_propagator test
        """
        parameters = {
                    "eccentricity": 0.0008641,
                    "semimajor_axis": 6801395.04,
                    "inclination": radians(87.0),
                    "perigee_argument": radians(20.0),
                    "right_ascension_of_ascending_node": radians(10.0),
                    "anomaly": radians(0.0),
                    "anomaly_type": "TRUE",
                    "orbit_update_date":'2021-12-02T00:00:00.000',
                    "frame": "EME"}
        k_orbit = keplerian_orbit(parameters)
        test1 = analytical_propagator(parameters)
        test2 = KeplerianPropagator(keplerian_orbit(parameters), Constants.WGS84_EARTH_MU)
        time1 = orekit_utils.absolute_time_converter_utc_string('2022-01-02T00:00:00.000')

        self.assertTrue(test1.getPVCoordinates(time1, FramesFactory.getEME2000()).toString() == test2.getPVCoordinates(time1, FramesFactory.getEME2000()).toString())


    def test_moving_body_pointing_law(self):
        """
        moving_body_pointing_law test
        """
        parameters = {
                    "eccentricity": 0.0008641,
                    "semimajor_axis": 6801395.04,
                    "inclination": 87.0,
                    "perigee_argument": 20.0,
                    "right_ascension_of_ascending_node": 10.0,
                    "anomaly": radians(0.0),
                    "anomaly_type": "TRUE",
                    "orbit_update_date":'2021-12-02T00:00:00.000',
                    "frame": "EME"}
        parameters1 = {
                    "eccentricity": 0.0008641,
                    "semimajor_axis": 6801395.04,
                    "inclination": 87.0,
                    "perigee_argument": 10.0,
                    "right_ascension_of_ascending_node": 10.0,
                    "anomaly": radians(0.0),
                    "anomaly_type": "TRUE",
                    "orbit_update_date":'2021-12-02T00:00:00.000',
                    "frame": "EME"}


        orbit_propagator_1 = analytical_propagator(parameters1)
        orbit_propagator_2 = analytical_propagator(parameters1)
        parameters["frame"] = orekit_utils.frame_to_string(orbit_propagator_1.getFrame())

        time_to_propagate = orekit_utils.absolute_time_converter_utc_string('2022-05-02T00:00:00.000')
        orbit_to_track_propagator = analytical_propagator(parameters)

        test1 = CelestialBodyPointed(FramesFactory.getEME2000(), orbit_to_track_propagator,
                                                Vector3D.PLUS_K, Vector3D.PLUS_K,
                                                Vector3D.MINUS_J)
        test2 = moving_body_pointing_law(orbit_to_track_propagator, parameters)

        orbit_propagator_1.setAttitudeProvider(test1)
        orbit_propagator_2.setAttitudeProvider(test2)
        state_1 = orbit_propagator_1.propagate(time_to_propagate)
        state_2 = orbit_propagator_2.propagate(time_to_propagate)
        self.assertTrue((state_1.getAttitude().getSpin().toString() == state_2.getAttitude().getSpin().toString()))

    def test_ground_pointing_law(self):
        """
        ground_pointing_law test
        """
        parameters = {
            "latitude": 12.0,
            "altitude": 2343.0,
            "longitude":12.0
        }
        parameters1 = {
                    "eccentricity": 0.0008641,
                    "semimajor_axis": 6801395.04,
                    "inclination": 87.0,
                    "perigee_argument": 10.0,
                    "right_ascension_of_ascending_node": 10.0,
                    "anomaly": radians(0.0),
                    "anomaly_type": "TRUE",
                    "orbit_update_date":'2021-12-02T00:00:00.000',
                    "frame": "EME"}

        orbit_propagator_1 = analytical_propagator(parameters1)
        orbit_propagator_2 = analytical_propagator(parameters1)
        parameters["frame"] = orekit_utils.frame_to_string(orbit_propagator_1.getFrame())


        ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
        target = GeodeticPoint(parameters["latitude"], parameters["longitude"], parameters["altitude"])
        attitude_provider = ground_pointing_law(parameters)
        attitude_provider_1 = TargetPointing(FramesFactory.getEME2000(), target, OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
                             Constants.WGS84_EARTH_FLATTENING,
                             ITRF))

        orbit_propagator_1.setAttitudeProvider(attitude_provider)
        orbit_propagator_2.setAttitudeProvider(attitude_provider_1)

        time_to_propagate = orekit_utils.absolute_time_converter_utc_string('2022-05-02T00:00:00.000')
        state_1 = orbit_propagator_1.propagate(time_to_propagate)
        state_2 = orbit_propagator_2.propagate(time_to_propagate)

        self.assertTrue((state_1.getAttitude().getSpin().toString() == state_2.getAttitude().getSpin().toString()))

    def test_attitude_provider_constructor(self):
        """
        attitude_provider_constructor test
        """
        moving_body = "moving_body_tracking"
        moving_body_param = {
                    "eccentricity": 0.0008641,
                    "semimajor_axis": 6801395.04,
                    "inclination": 87.0,
                    "perigee_argument": 10.0,
                    "right_ascension_of_ascending_node": 10.0,
                    "anomaly": 0.0,
                    "anomaly_type": "TRUE",
                    "orbit_update_date":"2021-12-02T00:00:00.000",
                    "frame": "EME"}

        orbit_params = {
                    "eccentricity": 0.0008641,
                    "semimajor_axis": 6801395.04,
                    "inclination": 87.0,
                    "perigee_argument": 20.0,
                    "right_ascension_of_ascending_node": 10.0,
                    "anomaly": 0.0,
                    "anomaly_type": "TRUE",
                    "orbit_update_date":'2021-12-02T00:00:00.000',
                    "frame": "EME"}

        orbit_propagator_1 = analytical_propagator(orbit_params)
        orbit_propagator_2 = analytical_propagator(orbit_params)

        attitude_m_body = attitude_provider_constructor(moving_body, moving_body_param)
        attitude_m_body_1 = moving_body_pointing_law(analytical_propagator(moving_body_param),moving_body_param)

        orbit_propagator_1.setAttitudeProvider(attitude_m_body)
        orbit_propagator_2.setAttitudeProvider(attitude_m_body_1)

        time_to_propagate = orekit_utils.absolute_time_converter_utc_string('2022-05-02T00:00:00.000')

        state_1 = orbit_propagator_1.propagate(time_to_propagate)
        state_2 = orbit_propagator_2.propagate(time_to_propagate)

        self.assertTrue((state_1.getAttitude().getSpin().toString() == state_2.getAttitude().getSpin().toString()))

        ground = "ground_tracking"
        ground_param = {
            "latitude": 12.0,
            "altitude": 2343.0,
            "longitude":12.0
            }
        parameters = {
                    "eccentricity": 0.0008641,
                    "semimajor_axis": 6801395.04,
                    "inclination": 87.0,
                    "perigee_argument": 10.0,
                    "right_ascension_of_ascending_node": 10.0,
                    "anomaly": radians(0.0),
                    "anomaly_type": "TRUE",
                    "orbit_update_date":'2021-12-02T00:00:00.000',
                    "frame": "EME"}

        orbit_propagator_1 = analytical_propagator(parameters)
        orbit_propagator_2 = analytical_propagator(parameters)
        ground_param["frame"] = orekit_utils.frame_to_string(orbit_propagator_1.getFrame())

        attitude_provider_1 = attitude_provider_constructor(ground, ground_param)
        attitude_provider_2 = ground_pointing_law(ground_param)

        orbit_propagator_1.setAttitudeProvider(attitude_provider_1)
        orbit_propagator_2.setAttitudeProvider(attitude_provider_2)

        time_to_propagate = orekit_utils.absolute_time_converter_utc_string('2022-05-02T00:00:00.000')
        state_1 = orbit_propagator_1.propagate(time_to_propagate)
        state_2 = orbit_propagator_2.propagate(time_to_propagate)

        self.assertTrue((state_1.getAttitude().getSpin().toString() == state_2.getAttitude().getSpin().toString()))

if __name__ == '__main__':
    unittest.main()

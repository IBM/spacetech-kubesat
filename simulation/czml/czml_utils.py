import json
import datetime
import kubesat.orekit as orekit_utils
from copy import deepcopy

def validate_datetime(date_text):
    try:
        datetime.datetime.strptime(date_text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")

        
def ISO8601_UTC(date):
    return f"{date[:19]}Z"


class Generic_CZML:

    def __init__(self, generic, start, duration):
        """
        Generate the initial CZML packets from boilerplate

        Args:
            generic (string JSON): CZML boilerplate, from the configuration in config-service
            start (string): the current time (from which the user wishes to display)
            duration ([type]): the duration of time after start that the user wishes to display, in seconds
        """
        generic = deepcopy(generic)

        stop = orekit_utils.absolute_time_converter_utc_string(start).shiftedBy(float(duration)).toString()
        start = ISO8601_UTC(start)
        stop = ISO8601_UTC(stop)
        
        validate_datetime(start)
        validate_datetime(stop)
        timestep = generic["timestep"]
        real_time = generic["real_time"]
        speed = int(timestep/real_time)
        generic1 = generic["generic_1"]
        generic1["clock"]["interval"] = f"{start}/{stop}"
        generic1["clock"]["currentTime"] = f"{start}"
        generic1["clock"]["multiplier"] = speed
        
        generic2 = generic["generic_2"]
        self.list = [generic1, generic2]


class CZML_Sat_Packet:

    def __init__(self, generic, name, start, duration, orbit):
        """
        Generate a standard CZML packet for displaying a satellite in Cesium, with configuration
        specified in "generic" argument

        Args:
            generic (string JSON): CZML boilerplate, from the configuration in config-service
            name (string): the name of the satellite the user wishes want to display
            start (string): the current time (from which the user wishes to display)
            duration (float): the duration of time after start that the user wishes to display, in seconds
            orbit (dict): dict containing the satellites keplerian orbital elements
        """

        generic = deepcopy(generic)
        # need to save before it is converted to a different format
        self.start = start
        stop = orekit_utils.absolute_time_converter_utc_string(start).shiftedBy(float(duration)).toString()
        
        start = ISO8601_UTC(start)
        stop = ISO8601_UTC(stop)
        
        validate_datetime(start)
        validate_datetime(stop)
        
        self.orbit = orbit
        self.name = name
        packet = {}
        _name = name.replace(" ", "_")
        self._name = name
        packet['id'] = f"Satellite/{_name}"
        packet['name'] = _name

        billboard = generic["billboard"]
        label = generic["label"]
        path = generic["path"]
        position = generic["position"]
        satellite_description = generic["satellite_description"]
    
        # set availability from the current date/time until a very long time in the future
        availability = f"{start}/{stop}"
        packet['availability'] = availability
        packet['description'] = satellite_description
        packet['billboard'] = billboard
        packet['label'] = label
        
        # record the correct name
        packet['label']['text'] = name
        
        # record the templates for updating later
        packet["path"] = path
        packet["position"] = position
        
        # make path viewable in correct time range
        #TODO edit this
        packet["path"]["show"][0]["interval"] = availability

        self.packet = packet
    

    def update_orbit(self, orbit):
        """
        Generate a new orbit packet, with duration as specified in the constructor.

        Args:
            orbit (dict): A nested python dictionary with orbital parameters.
        """
        new_date = orekit_utils.absolute_time_converter_utc_string(orbit["orbit_update_date"])
        old_date = orekit_utils.absolute_time_converter_utc_string(self.orbit["orbit_update_date"])
        if new_date.isAfter(old_date):
            self.orbit = orbit


    def calculate_position(self, generic, duration, step_count=None):
        """ 
        Updates position of the satellite for some number of time steps into the future,
        and update the packet to contain Cartesian coordinates

        Args:
            generic (string JSON): CZML boilerplate, from the configuration in config-service
            duration (float): the duration of time after start that the user wishes to display, in seconds
            step_count (int): number of positions to include in the packet. Note - Cesium has 5th-order Lagrangian interpolation. 300.0 sec is fine
        """
        # Default step count defined in terms of duration
        generic = deepcopy(generic)

        if step_count==None:
            step_count = int(duration/300)
        
        step_size = float(duration/step_count)
        stop = orekit_utils.absolute_time_converter_utc_string(self.start).shiftedBy(float(duration)).toString()
        start = ISO8601_UTC(self.start)
        stop = ISO8601_UTC(stop)
        
        validate_datetime(start)
        validate_datetime(stop)
        
        self.packet["availability"] = f"{start}/{stop}"
        self.packet["position"]["epoch"] = start
        
        prop = orekit_utils.analytical_propagator(self.orbit)
        positions = []
        for i in range(step_count):
            orekit_time = orekit_utils.absolute_time_converter_utc_string(start).shiftedBy(i * float(step_size))
            pos = prop.getPVCoordinates(orekit_time, prop.getFrame())
            pos = list(pos.position.toArray())
            pos.insert(0,i * float(step_size))
            positions.extend(pos)
        self.packet["position"]["cartesian"] = positions
        
        # TODO
        lead_trail_time = orekit_utils.absolute_time_converter_utc_string(start).shiftedBy(generic["lead_and_trail"]).toString()
        lead_trail_time = ISO8601_UTC(lead_trail_time)
        
        validate_datetime(lead_trail_time)
        
        interval =  f"{start}/{lead_trail_time}"
        
        lead_and_trail = ["leadTime", "trailTime"]

        for lt in lead_and_trail:
            self.packet["path"][lt].append({})
            self.packet["path"][lt][0]["interval"] = interval
            self.packet["path"][lt][0]["epoch"] = start
            self.packet["path"][lt][0]["number"] = [0, generic["lead_and_trail_number"], generic["lead_and_trail_number"], 0]



class CZML_Grstn_Packet:

    def __init__(self, generic, name, start, duration, location):
        """ 
        Construct a ground station packet.

        Args:
            generic (string JSON): CZML boilerplate, from the configuration in config-service
            name (string): the name of the ground station the user wishes want to display
            start (string): the current time (from which the user wishes to display)
            duration (float): the duration of time after start that the user wishes to display, in seconds. This should be a big number if the user doesn't want it to disappear.
            location (dict): dictionary containing float latitude, longitude, and altitude of the ground station
        """
        generic = deepcopy(generic)

        latitude = location["latitude"]
        longitude = location["longitude"]
        altitude = location["altitude"]
        
        self.start = start
        stop = orekit_utils.absolute_time_converter_utc_string(start).shiftedBy(float(duration)).toString()
        start = ISO8601_UTC(start)
        stop = ISO8601_UTC(stop)
        
        validate_datetime(start)
        validate_datetime(stop)
        
        _name = name.replace(" ", "_")
        
        self.packet = generic["grstn"]
        self.packet["id"] = f"Facility/{_name}"
        self.packet["name"] = _name
        self.packet["availability"] = f"{start}/{stop}"
        self.packet["position"]["cartographicDegrees"] = [float(longitude), float(latitude), float(altitude)]
        self.packet["label"]["text"] = name


class CZML_Sat_2_Grnd_Link_Packet:

    def __init__(self, generic, sat_name, grstn_name, start, sat_orbit, grstn_location):
        """ 
        Initialize a satellite to ground link generator.

        Args:
            generic (string JSON): CZML boilerplate, from the configuration in config-service
            sat_name (string): the name of the satellite the user wishes want to display
            grstn_name (string): the name of the ground station the user wishes want to display
            start (string): the current time (from which the user wishes to display)
            sat_orbit (dict): A nested python dictionary with orbital parameters.
            grstn_location (dict): dictionary containing float latitude, longitude, and altitude of the ground station
        """
        generic = deepcopy(generic)
        _grstn_name = grstn_name.replace(" ", "_")
        _sat_name = sat_name.replace(" ", "_")
        
        self.start = start
        self.sat_orbit = sat_orbit
        self.grstn_location = grstn_location
        self.packet = generic["sat2grstn"]
        self.packet["id"] = f"Facility/{_grstn_name}-to-Satellite/{_sat_name}"
        self.packet["name"] = f"{grstn_name} to {sat_name}"
        self.packet["polyline"]["positions"] = [
            f"Facility/{_grstn_name}#position", f"Satellite/{_sat_name}#position"
        ]
        
    def update_orbit(self, orbit):
        """ 
        Generate a new orbit packet, with duration as specified in the constructor.

        Args:
            orbit (dict): A nested python dictionary with orbital parameters.
        """
        new_date = orekit_utils.absolute_time_converter_utc_string(orbit["orbit_update_date"])
        old_date = orekit_utils.absolute_time_converter_utc_string(self.orbit["orbit_update_date"])
        if new_date.isAfter(old_date):
            self.sat_orbit = orbit

    def update_packet(self, duration):
        """ 
        Update the packet attributre

        Args:
            duration (float): the duration of time after start that the user wishes to display, in seconds. This should be a big number if the user doesn't want it to disappear.
        """
        
        start = self.start
        orbit = self.sat_orbit
        grstn_latitude = self.grstn_location["latitude"]
        grstn_longitude = self.grstn_location["longitude"]
        grstn_altitude = self.grstn_location["altitude"]
        
        start_orekit = orekit_utils.absolute_time_converter_utc_string(start)
        stop_orekit = orekit_utils.absolute_time_converter_utc_string(start).shiftedBy(float(duration))
        
        prop = orekit_utils.analytical_propagator(orbit)
        eclipses = orekit_utils.get_ground_passes(prop, grstn_latitude, grstn_longitude, grstn_altitude, start_orekit, stop_orekit, ploting_param=False)
        
        if len(eclipses):
            self.packet["polyline"]["show"].append({})
            
            if not eclipses[0]['start']:
                eclipses[0]['start'] = start_orekit
            first_end = ISO8601_UTC(eclipses[0]['start'].toString())
            validate_datetime(first_end)
            
            self.packet["polyline"]["show"][0]["interval"] = f"0000-01-01T00:00:00/{first_end}"
            self.packet["polyline"]["show"][0]["boolean"] = False
            
            for i,d in enumerate(eclipses):
                show = {}
                start_vis = ISO8601_UTC(d['start'].toString())
                stop_vis = ISO8601_UTC(d['stop'].toString())
                
                validate_datetime(start_vis)
                validate_datetime(stop_vis)
                
                visible_interval = f"{start_vis}/{stop_vis}"
                show["interval"] = visible_interval
                show["boolean"] = True
                self.packet["polyline"]["show"].append(show)
                self.packet["availability"].append(visible_interval)
                
                # only add the period after if it is with the stop time
                if i + 1 < len(eclipses):
                    dont_show = {}
                    last_interval_start = ISO8601_UTC(eclipses[i]['stop'].toString())
                    last_interval_stop = ISO8601_UTC(eclipses[i+1]['start'].toString())
                    
                    validate_datetime(last_interval_start)
                    validate_datetime(last_interval_stop)
                    
                    dont_show["interval"] = f"{last_interval_start}/{last_interval_stop}"
                    dont_show["boolean"] = False
                    self.packet["polyline"]["show"].append(dont_show)


class CZML_Sat_2_Sat_Link_Packet:
    """ 
        Initialize a satellite to satellite link generator.

        Args:
            shared_storage (string JSON): Dictionary containing information on orbits of satellites
            duration (float): the duration of time after start that the user wishes to display, in seconds. This should be a big number if the user doesn't want it to disappear.
        """

    def __init__(self, shared_storage, duration):
        """ 
        Initialize a Satellite to Satellite link packet object

        Args:
            shared_storage (dict): a CZML shared storage object (schema in config-service)
            duration (float): the duration of time after start that the user wishes to display, in seconds.
        """
        self.packets = []
        self.shared_storage = shared_storage
        self.duration = duration
        self.satellite_links = self.create_set()
    
    def create_set(self):
        """
        Function that creates a set of the titles of all the satellite to satellite links

        Returns:
            set: a set of the titles of all the satellite to satellite links
        """
        swarm  = self.shared_storage["swarm"]
        satellite_links = set()
        for i in swarm:
            for j in swarm:
                if i == j:
                    continue
                a = [i,j]
                a.sort()
                link = "Satellite/" + a[0] + "-to-Satellite/" + a[1]
                satellite_links.add(link)
        return satellite_links
    
    def process_time_window(self, windows_array):
        """
        Function that transforms an array of times when satellites will be able to talk to eachother
        into a format that can be understood by cesium

        Args:
            windows_array (list): list of times when satellites will be able to talk to eachother

        Returns:
            [Array]: list of times that satellites will and won't be able to talk to eachother
        """
        n_windows_array = []
        if len(windows_array) == 0:
            return ['0000-01-01T00:00:00Z/9999-12-31T24:00:00Z']
        for i in range(len(windows_array)):
            if i == 0:
                n_windows_array.append('0000-01-01T00:00:00Z/'+ windows_array[i][0].toString()[:19]+'Z')
                n_windows_array.append(windows_array[i][0].toString()[:19]+'Z/'+ windows_array[i][1].toString()[:19]+'Z')
            else:  
                n_windows_array.append(windows_array[i-1][1].toString()[:19]+'Z/'+ windows_array[i][0].toString()[:19]+'Z')
                n_windows_array.append(windows_array[i][0].toString()[:19]+'Z/'+ windows_array[i][1].toString()[:19]+'Z')

            if i == len(windows_array) - 1:
                n_windows_array.append(windows_array[i][1].toString()[:19]+'Z/9999-12-31T24:00:00Z')
        return n_windows_array
           
             
    def create_availability(self, show):
        """
        Creates availability list that can be read by cesium given an list of times of when to show the
        links between satellites

        Args:
            show (list): list of times when to show links

        Returns:
            list: a list containing the availability of the inter satellite links to be read by cesium
        """
        availability = []
        for i in show:
            if i["boolean"]:
                availability.append(i["interval"])
        return availability   
    
    def create_show(self, n_windows_array):
        """
        Given an list of times to show and not show an inter satellite link, a new list of dictionaries
        to be read by cesium

        Args:
            n_windows_array (list): list of times to show and not show an inter satellite link

        Returns:
            list: list of dictionaries containing information on when to show and not show inter satellite\
                  links
        """
        show = []
        for i in range(len(n_windows_array)):
            new_dict = {"interval":n_windows_array[i]}
            if i % 2 == 0:
                new_dict["boolean"] = False
            else:
                new_dict["boolean"] = True
            show.append(new_dict)
        return show
        
    def produce_links(self, save=False, new_shared_storage = None):
        """
        

        Args:
            save (bool, optional): Wether or not the packets should be saved. Defaults to True.
            new_shared_storage (dictionary, optional): A new dictionary containing satellite orbits,
            iot sensors, and groundstation to be used. Defaults to None.

        Returns:
            list: list of all of the inter satellite link packets
        """
        if new_shared_storage == None:
            shared_storage = self.shared_storage
        else:
            shared_storage = new_shared_storage
        satellite_links = self.satellite_links
        packet_links = []
        # for each element in the satellite links set make a packet
        for i in satellite_links:
            # find the names
            cubesat_a = i[i.find('/')+1:i.find('-')]
            cubesat_b = i[i.rfind('/')+1:]

            # create a orbit propagator for both satellites
            csat_a_prop = orekit_utils.analytical_propagator(shared_storage["swarm"][cubesat_a]["orbit"])
            csat_b_prop = orekit_utils.analytical_propagator(shared_storage["swarm"][cubesat_b]["orbit"])

            # create a list of times when the satellites can see each other
            start_time = orekit_utils.absolute_time_converter_utc_string(shared_storage["time"])            
            windows_array = orekit_utils.visible_above_horizon(csat_a_prop, csat_b_prop, start_time, self.duration)

            # create a list of times when the satellites can see and not see each other
            n_windows_array = self.process_time_window(windows_array)

            # create a list of objects when the satellite links can be shown for cesium
            show = self.create_show(n_windows_array)

            # create a list of times when the satellites can see and not see each other for cesium
            availability = self.create_availability(show)

            references = [i[:i.find("-to-")]+'#position', i[i.find("-to-") + 4:]+'#position']

            # Construct the packet with a generic link packet and data created above
            packet = deepcopy(self.shared_storage["generic"]["general_link"])
            packet["id"] = i
            packet["name"] = cubesat_a +" to " + cubesat_b
            packet["availability"] = availability
            packet["description"] = "<h1>Blah blah blah</h1>"   
            packet["polyline"]["show"] = show
            packet["polyline"]["positions"]["references"] = references
            packet_links.append(packet)
        # save as json if 
        if save:
            with open('data.json', 'w') as outfile:
                json.dump(packet_links, outfile)
        self.packets = packet_links
        return packet_links
        
        

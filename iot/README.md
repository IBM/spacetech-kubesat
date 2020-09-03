## IOT Service Repository
Maintains IOT service for ground sensors and manages their communications. The iot service receives timestep messages from the clock and then creates a variety of fake data and then broadcasts it to the data service. Currently, it broadcats fake agriculture data, but it could be adapted to send real data or any type of data in the future.

### Callbacks

| **Function Name**      | Purpose                                                                                      |
|------------------------|----------------------------------------------------------------------------------------------|
| **send_data**          | Randomly generates temperature data from a sin wave every timestep and broadcasts it.        |
| **soil_water_content** | Randomly generates soil water content data from a sin wave every timestep and broadcasts it. |
| **fertilizer_level**   | Randomly generates fertilizer level data from a sin wave every timestep and broadcasts it.   |

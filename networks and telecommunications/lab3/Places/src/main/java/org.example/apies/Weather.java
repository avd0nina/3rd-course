package org.example.apies;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;

public class Weather {
    private final String weatherState;
    private final double temp;
    private final double tempFeelLike;
    private final double pressure;
    private final double humidity;
    private final double windSpeed;
    private final double cloud;

    public Weather(JSONObject obj) {
        weatherState = (String) ((JSONObject) ((JSONArray) obj.get("weather")).get(0)).get("main");
        temp = getValue(obj, "main", "temp");
        tempFeelLike = getValue(obj, "main", "feels_like");
        windSpeed = getValue(obj, "wind", "speed");
        pressure = getValue(obj, "main", "pressure") * 0.75;
        humidity = getValue(obj, "main", "humidity");
        cloud = getValue(obj, "clouds", "all");
    }

    private double getValue(JSONObject obj, String first, String second) {
        return Double.parseDouble(String.valueOf(((JSONObject) obj.get(first)).get(second)));
    }

    @Override
    public String toString() {
        return String.format("""
                        Current weather: %s,
                            Temperature: %.2f C, feels like: %.2f C
                            Pressure: %.0f mm.Hg
                            Humidity: %.0f %%
                            Wind speed: %.2f m/s
                            Cloud percent: %.0f %%
                        """,
                weatherState, temp, tempFeelLike, pressure, humidity, windSpeed, cloud);
    }
}

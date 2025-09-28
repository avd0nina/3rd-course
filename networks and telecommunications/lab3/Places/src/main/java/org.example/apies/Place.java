package org.example.apies;

import lombok.Getter;
import org.jetbrains.annotations.NotNull;
import org.json.simple.JSONObject;
import java.nio.charset.StandardCharsets;

@SuppressWarnings({"FieldCanBeLocal","unused"})
public class Place {
    private final String country;
    private final String osm_key;
    private final String osm_value;
    private final String city;
    private final String street;
    private final String name;
    @Getter
    private final double latitude;
    @Getter
    private final double longitude;

    public Place(JSONObject obj) {
        country = get("country", obj);
        osm_key = get("osm_key", obj);
        osm_value = get("osm_value", obj);
        city = get("city", obj);
        street = get("street", obj);
        name = get("name", obj);
        latitude = (double) ((JSONObject) obj.get("point")).get("lat");
        longitude = (double) ((JSONObject) obj.get("point")).get("lng");
    }

    private static String get(String key, @NotNull JSONObject obj) {
        return obj.get(key) != null ? (String) obj.get(key) : "Unknown";

    }

    @Override
    public String toString() {
        return new String(String.format("Name of place: %s, class: %s, type: %s, country: %s, city: %s",
                name, osm_key, osm_value, country, city).getBytes(StandardCharsets.UTF_8));
    }
}

package org.example.apies;

import lombok.Getter;
import org.jetbrains.annotations.NotNull;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;

import java.nio.charset.StandardCharsets;

public class InterestingPlace {
    private final String name;
    @Getter
    private final String xid;
    private final double latitude;
    private final double longitude;
    private String info;

    public InterestingPlace(@NotNull JSONObject feature) {
        name = (String) ((JSONObject) feature.get("properties")).get("name");
        xid = (String) ((JSONObject) feature.get("properties")).get("xid");
        longitude = (double) ((JSONArray) ((JSONObject) feature.get("geometry")).get("coordinates")).get(0);
        latitude = (double) ((JSONArray) ((JSONObject) feature.get("geometry")).get("coordinates")).get(1);
    }

    public void setInfo(@NotNull JSONObject obj) {
        if (obj.get("wikipedia_extracts") != null) {
            info = (String) ((JSONObject) obj.get("wikipedia_extracts")).get("text");
        } else {
            info = "Information absent";
        }
    }

    @Override
    public String toString() {
        return new String(String.format("""
                        Interesting place: %s
                            Latitude: %.3f, longitude: %.3f
                            Info: %s
                        """,
                name, latitude, longitude, info).getBytes(StandardCharsets.UTF_8));
    }
}

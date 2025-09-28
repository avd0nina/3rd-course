package org.example;

import org.jetbrains.annotations.Contract;
import org.jetbrains.annotations.NotNull;
import org.example.apies.APiKeys;
import org.example.apies.InterestingPlace;
import org.example.apies.Place;

public class URLUtils {
    @NotNull
    @Contract(pure = true)
    public static String getLocationVariantsURL(String placeName, int limit) {
        return "https://graphhopper.com/api/1/geocode?" +
                "q=" + placeName +
                "&key=" + APiKeys.locationApiKey +
                "&limit=" + limit +
                "&locale=en";
    }

    @NotNull
    @Contract(pure = true)
    public static String getWeatherURL(@NotNull Place selectPlace) {
        return "https://api.openweathermap.org/data/2.5/weather?" +
                "lat=" + selectPlace.getLatitude() +
                "&lon=" + selectPlace.getLongitude() +
                "&units=metric" +
                "&appid=" + APiKeys.weatherApiKey;
    }

    @NotNull
    @Contract(pure = true)
    public static String getInterestLocationURL(@NotNull Place selectPlace, int radius) {
        return "https://api.opentripmap.com/0.1/en/places/radius?" +
                "radius=" + radius +
                "&lon=" + selectPlace.getLongitude() +
                "&lat=" + selectPlace.getLatitude() +
                "&apikey=" + APiKeys.interestLocationApiKey;
    }

    @NotNull
    @Contract(pure = true)
    public static String getInterestLocationInfoURL(@NotNull InterestingPlace interestingPlace) {
        return "https://api.opentripmap.com/0.1/en/places/" +
                "xid/" + interestingPlace.getXid() +
                "?apikey=" + APiKeys.interestLocationApiKey;
    }
}

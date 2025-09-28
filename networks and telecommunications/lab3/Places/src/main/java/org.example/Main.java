package org.example;

import lombok.extern.slf4j.Slf4j;
import org.jetbrains.annotations.NotNull;
import java.util.NoSuchElementException;
import java.util.Scanner;

@Slf4j
public class Main {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        System.out.println("Insert place name: ");
        String placeName = scanner.nextLine();
        System.out.println("Insert count of interesting places, which you want to see: ");
        int limit = getValue(scanner, "count of interesting places");
        System.out.println("Insert radius where interesting places will be searched: ");
        int radius = getValue(scanner, "radius");
        LocationFinder locationFinder = new LocationFinder(placeName, limit, radius);
        locationFinder.start();
        scanner.close();
    }

    private static int getValue(@NotNull Scanner scanner, String valueInfo) {
        int value;
        while (true) {
            try {
                value = Integer.parseInt(scanner.nextLine());
                if (value <= 0) {
                    System.out.printf("Insert correct (>0) %s:\n", valueInfo);
                } else {
                    break;
                }
            } catch (NoSuchElementException | NumberFormatException e) {
                System.out.printf("Insert integer %s:\n", valueInfo);
            }
        }
        return value;
    }
}

package org.example;

import org.example.model.Model;
import java.util.logging.Logger;

public class Main {
    public static void main(String[] args) {
        Logger logger = Logger.getLogger(Main.class.getSimpleName());
        logger.info("Game is starting!" );

        new Model();
    }
}

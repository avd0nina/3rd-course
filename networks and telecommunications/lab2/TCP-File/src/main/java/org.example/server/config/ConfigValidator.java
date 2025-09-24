package org.example.server.config;

public interface ConfigValidator {
    void validate(ServerConfiguration serverConfiguration) throws ConfigException;
}

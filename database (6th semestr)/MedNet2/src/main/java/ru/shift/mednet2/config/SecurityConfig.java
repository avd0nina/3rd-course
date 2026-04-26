package ru.shift.mednet2.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.beans.factory.annotation.Value;
import java.util.Arrays;
import java.util.List;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

@Configuration
public class SecurityConfig {

    @Value("${app.cors.allowed-origins:http://localhost:5173}")
    private String allowedOrigins;

    @Bean
    SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        return http
                .csrf(AbstractHttpConfigurer::disable)
                .cors(Customizer.withDefaults())
                .authorizeHttpRequests(authorize -> authorize
                        .requestMatchers("/api/v1/auth/me", "/api/v1/catalog/**").authenticated()
                        .requestMatchers("/api/v1/reports/laboratory/productivity").hasAnyRole("ADMIN_SYSTEM", "LABORATORY_SPECIALIST")
                        .requestMatchers("/api/v1/reports/**").hasRole("ADMIN_SYSTEM")
                        .requestMatchers("/api/v1/**").hasRole("ADMIN_SYSTEM")
                        .anyRequest().permitAll())
                .httpBasic(Customizer.withDefaults())
                .build();
    }

    @Bean
    UserDetailsService userDetailsService() {
        return new InMemoryUserDetailsManager(
                User.withUsername("sys_admin")
                        .password("{noop}SysAdmin2026")
                        .roles("ADMIN_SYSTEM")
                        .build(),
                User.withUsername("admin")
                        .password("{noop}admin")
                        .roles("ADMIN_SYSTEM")
                        .build(),
                User.withUsername("lab_sidorov")
                        .password("{noop}LabSidor2026")
                        .roles("LABORATORY_SPECIALIST")
                        .build(),
                User.withUsername("lab")
                        .password("{noop}lab")
                        .roles("LABORATORY_SPECIALIST")
                        .build()
        );
    }

    @Bean
    CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        List<String> origins = Arrays.stream(allowedOrigins.split(","))
                .map(String::trim)
                .filter(origin -> !origin.isBlank())
                .toList();
        configuration.setAllowedOrigins(origins);
        configuration.setAllowedMethods(List.of("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(List.of("*"));
        configuration.setAllowCredentials(true);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}

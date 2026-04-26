package ru.shift.mednet2.security;

import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;

public enum AppRole {
    ADMIN_SYSTEM("ROLE_ADMIN_SYSTEM", "Администратор системы"),
    LABORATORY_SPECIALIST("ROLE_LABORATORY_SPECIALIST", "Специалист лабораторий");

    private final String authority;
    private final String displayName;

    AppRole(String authority, String displayName) {
        this.authority = authority;
        this.displayName = displayName;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getCode() {
        return name();
    }

    public static AppRole fromAuthentication(Authentication authentication) {
        if (authentication == null || authentication.getAuthorities() == null) {
            throw new AccessDeniedException("Требуется авторизация");
        }

        return authentication.getAuthorities()
                .stream()
                .map(grantedAuthority -> grantedAuthority.getAuthority())
                .filter(authority -> authority != null && !authority.isBlank())
                .map(AppRole::fromAuthority)
                .findFirst()
                .orElseThrow(() -> new AccessDeniedException("Роль пользователя не поддерживается"));
    }

    private static AppRole fromAuthority(String authority) {
        for (AppRole role : values()) {
            if (role.authority.equals(authority)) {
                return role;
            }
        }
        throw new AccessDeniedException("Недопустимая роль: " + authority);
    }
}

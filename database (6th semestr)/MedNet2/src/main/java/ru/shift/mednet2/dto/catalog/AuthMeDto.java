package ru.shift.mednet2.dto.catalog;

public record AuthMeDto(
        String username,
        String roleKey,
        String roleName
) {
}

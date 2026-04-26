package ru.shift.mednet2.dto.catalog;

public record TablePermissionDto(
        boolean canRead,
        boolean canCreate,
        boolean canUpdate,
        boolean canDelete
) {
}

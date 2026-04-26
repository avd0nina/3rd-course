package ru.shift.mednet2.dto.catalog;

public record TableMetaDto(
        String key,
        String tableName,
        String title,
        String idColumn,
        TablePermissionDto permissions
) {
}

package ru.shift.mednet2.dto.catalog;

import java.util.List;
import java.util.Map;

public record TableRowsDto(
        List<ColumnMetaDto> columns,
        List<Map<String, Object>> rows,
        TablePermissionDto permissions
) {
}

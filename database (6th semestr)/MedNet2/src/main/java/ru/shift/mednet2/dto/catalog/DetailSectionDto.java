package ru.shift.mednet2.dto.catalog;

import java.util.List;
import java.util.Map;

public record DetailSectionDto(
        String tableKey,
        String title,
        List<Map<String, Object>> rows
) {
}

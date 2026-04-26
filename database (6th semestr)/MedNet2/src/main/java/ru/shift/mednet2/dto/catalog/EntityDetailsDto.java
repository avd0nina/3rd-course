package ru.shift.mednet2.dto.catalog;

import java.util.List;

public record EntityDetailsDto(
        String title,
        List<DetailSectionDto> sections
) {
}

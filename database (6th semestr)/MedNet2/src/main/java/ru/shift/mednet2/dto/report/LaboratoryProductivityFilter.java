package ru.shift.mednet2.dto.report;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;
import lombok.Getter;
import lombok.Setter;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.format.annotation.DateTimeFormat.ISO;

@Getter
@Setter
public class LaboratoryProductivityFilter {

    @Min(value = 1, message = "institutionId must be greater than 0")
    private Integer institutionId;

    private String city;

    @NotNull(message = "startDate is required")
    @DateTimeFormat(iso = ISO.DATE)
    private LocalDate startDate;

    @NotNull(message = "endDate is required")
    @DateTimeFormat(iso = ISO.DATE)
    private LocalDate endDate;
}

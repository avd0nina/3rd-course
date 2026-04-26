package ru.shift.mednet2.dto.report;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.time.LocalDate;
import lombok.Getter;
import lombok.Setter;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.format.annotation.DateTimeFormat.ISO;

@Getter
@Setter
public class PatientOperationsFilter {

    @Min(value = 1, message = "institutionId must be greater than 0")
    private Integer institutionId;

    @Pattern(
            regexp = "Hospital|Polyclinic|Laboratory",
            message = "institutionType must be one of: Hospital, Polyclinic, Laboratory"
    )
    private String institutionType;

    @Min(value = 1, message = "doctorId must be greater than 0")
    private Integer doctorId;

    @NotNull(message = "startDate is required")
    @DateTimeFormat(iso = ISO.DATE)
    private LocalDate startDate;

    @NotNull(message = "endDate is required")
    @DateTimeFormat(iso = ISO.DATE)
    private LocalDate endDate;
}


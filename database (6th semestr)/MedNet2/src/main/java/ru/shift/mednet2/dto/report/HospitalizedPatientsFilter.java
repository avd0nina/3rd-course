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
public class HospitalizedPatientsFilter {

    @Min(value = 1, message = "hospitalId must be greater than 0")
    private Integer hospitalId;

    @Min(value = 1, message = "doctorId must be greater than 0")
    private Integer doctorId;

    @NotNull(message = "startDate is required")
    @DateTimeFormat(iso = ISO.DATE)
    private LocalDate startDate;

    @NotNull(message = "endDate is required")
    @DateTimeFormat(iso = ISO.DATE)
    private LocalDate endDate;
}


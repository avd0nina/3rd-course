package ru.shift.mednet2.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.time.LocalDate;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class OperationDto {

    private Integer operationId;

    @NotNull(message = "patientId is required")
    @Min(value = 1, message = "patientId must be > 0")
    private Integer patientId;

    @NotNull(message = "doctorId is required")
    @Min(value = 1, message = "doctorId must be > 0")
    private Integer doctorId;

    @NotNull(message = "typeId is required")
    @Min(value = 1, message = "typeId must be > 0")
    private Integer typeId;

    private LocalDate plannedDate;

    @NotNull(message = "performedDate is required")
    private LocalDate performedDate;

    @NotBlank(message = "outcome is required")
    @Pattern(
            regexp = "(?i)success|fatal|complications|canceled",
            message = "outcome must be one of: success, fatal, complications, canceled"
    )
    private String outcome;

    private String description;
}

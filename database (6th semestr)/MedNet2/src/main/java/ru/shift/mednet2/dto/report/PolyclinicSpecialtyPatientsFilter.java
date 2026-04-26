package ru.shift.mednet2.dto.report;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class PolyclinicSpecialtyPatientsFilter {

    @NotBlank(message = "specialty is required")
    private String specialty;

    @NotNull(message = "polyclinicId is required")
    @Min(value = 1, message = "polyclinicId must be greater than 0")
    private Integer polyclinicId;
}


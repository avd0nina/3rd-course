package ru.shift.mednet2.dto.report;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class DoctorsByOperationsFilter extends SpecialtyInstitutionFilter {

    @NotNull(message = "minOperations is required")
    @Min(value = 0, message = "minOperations must be >= 0")
    private Integer minOperations;
}

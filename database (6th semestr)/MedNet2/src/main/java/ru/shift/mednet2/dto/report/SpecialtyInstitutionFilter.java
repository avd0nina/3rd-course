package ru.shift.mednet2.dto.report;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class SpecialtyInstitutionFilter {

    @NotBlank(message = "specialty is required")
    private String specialty;

    @Min(value = 1, message = "institutionId must be greater than 0")
    private Integer institutionId;

    @Pattern(
            regexp = "Hospital|Polyclinic|Laboratory",
            message = "institutionType must be one of: Hospital, Polyclinic, Laboratory"
    )
    private String institutionType;

    private String city;
}

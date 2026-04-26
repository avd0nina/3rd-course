package ru.shift.mednet2.dto.report;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class DoctorsByExperienceFilter extends SpecialtyInstitutionFilter {

    @NotNull(message = "minExperience is required")
    @Min(value = 0, message = "minExperience must be >= 0")
    private Integer minExperience;
}


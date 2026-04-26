package ru.shift.mednet2.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class SpecialtyDto {

    private Integer specialtyId;

    @NotBlank(message = "name is required")
    private String name;

    @NotNull(message = "vacationDays is required")
    @Min(value = 28, message = "vacationDays must be >= 28")
    private Integer vacationDays;

    @NotNull(message = "baseSalary is required")
    @Min(value = 1, message = "baseSalary must be > 0")
    private Integer baseSalary;

    @NotNull(message = "hazardCoefficient is required")
    @DecimalMin(value = "0.0", inclusive = false, message = "hazardCoefficient must be > 0")
    private Double hazardCoefficient;
}

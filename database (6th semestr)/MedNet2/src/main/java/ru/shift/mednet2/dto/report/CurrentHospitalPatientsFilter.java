package ru.shift.mednet2.dto.report;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class CurrentHospitalPatientsFilter {

    @NotNull(message = "hospitalId is required")
    @Min(value = 1, message = "hospitalId must be greater than 0")
    private Integer hospitalId;

    @Min(value = 1, message = "departmentId must be greater than 0")
    private Integer departmentId;

    @Min(value = 1, message = "wardId must be greater than 0")
    private Integer wardId;

    @Min(value = 1, message = "wardNumber must be greater than 0")
    private Integer wardNumber;
}


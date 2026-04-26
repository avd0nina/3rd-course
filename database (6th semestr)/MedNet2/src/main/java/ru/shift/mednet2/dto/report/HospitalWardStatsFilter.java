package ru.shift.mednet2.dto.report;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class HospitalWardStatsFilter {

    @NotNull(message = "hospitalId is required")
    @Min(value = 1, message = "hospitalId must be greater than 0")
    private Integer hospitalId;
}


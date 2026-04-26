package ru.shift.mednet2.dto.report;

import jakarta.validation.constraints.Min;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class DoctorLoadFilter {

    @Min(value = 1, message = "doctorId must be greater than 0")
    private Integer doctorId;

    @Min(value = 1, message = "hospitalId must be greater than 0")
    private Integer hospitalId;

    private String specialty;
}


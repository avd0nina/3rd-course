package ru.shift.mednet2.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class EmployeeDto {

    private Integer employeeId;

    @NotBlank(message = "fullName is required")
    private String fullName;
}

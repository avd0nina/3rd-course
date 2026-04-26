package ru.shift.mednet2.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class PatientDto {

    private Integer patientId;

    @NotBlank(message = "fullName is required")
    private String fullName;

    @NotNull(message = "birthDate is required")
    private LocalDate birthDate;

    @NotBlank(message = "address is required")
    private String address;

    @NotNull(message = "polyclinicId is required")
    @Min(value = 1, message = "polyclinicId must be > 0")
    private Integer polyclinicId;

    private String omsNumber;
    private String snils;
    private String passportData;
    private String phoneNumber;
}

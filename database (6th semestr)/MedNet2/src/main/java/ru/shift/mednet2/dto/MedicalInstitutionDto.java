package ru.shift.mednet2.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class MedicalInstitutionDto {

    private Integer institutionId;

    @NotBlank(message = "name is required")
    private String name;

    @NotBlank(message = "address is required")
    private String address;

    @NotBlank(message = "type is required")
    @Pattern(
            regexp = "(?i)Hospital|Polyclinic|Laboratory",
            message = "type must be one of: Hospital, Polyclinic, Laboratory"
    )
    private String type;
}

package ru.shift.mednet2.controller;

import jakarta.validation.Valid;
import java.util.List;
import java.util.Map;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import ru.shift.mednet2.dto.report.CurrentHospitalPatientsFilter;
import ru.shift.mednet2.dto.report.DoctorLoadFilter;
import ru.shift.mednet2.dto.report.DoctorProductivityFilter;
import ru.shift.mednet2.dto.report.DoctorsByExperienceFilter;
import ru.shift.mednet2.dto.report.DoctorsByOperationsFilter;
import ru.shift.mednet2.dto.report.HospitalWardStatsFilter;
import ru.shift.mednet2.dto.report.HospitalizedPatientsFilter;
import ru.shift.mednet2.dto.report.LaboratoryProductivityFilter;
import ru.shift.mednet2.dto.report.PatientOperationsFilter;
import ru.shift.mednet2.dto.report.PolyclinicOfficeVisitsFilter;
import ru.shift.mednet2.dto.report.PolyclinicSpecialtyPatientsFilter;
import ru.shift.mednet2.dto.report.SpecialtyInstitutionFilter;
import ru.shift.mednet2.service.ReportService;

@RestController
@RequestMapping("/api/v1/reports")
@Validated
public class ReportController {

    private final ReportService reportService;

    public ReportController(ReportService reportService) {
        this.reportService = reportService;
    }

    @GetMapping("/doctors/specialty")
    public List<Map<String, Object>> doctorsBySpecialty(@Valid @ModelAttribute SpecialtyInstitutionFilter filter) {
        return reportService.doctorsBySpecialty(filter);
    }

    @GetMapping("/staff/specialty")
    public List<Map<String, Object>> supportStaffBySpecialty(@Valid @ModelAttribute SpecialtyInstitutionFilter filter) {
        return reportService.supportStaffBySpecialty(filter);
    }

    @GetMapping("/doctors/operations")
    public List<Map<String, Object>> doctorsByOperations(@Valid @ModelAttribute DoctorsByOperationsFilter filter) {
        return reportService.doctorsByOperations(filter);
    }

    @GetMapping("/doctors/experience")
    public List<Map<String, Object>> doctorsByExperience(@Valid @ModelAttribute DoctorsByExperienceFilter filter) {
        return reportService.doctorsByExperience(filter);
    }

    @GetMapping("/doctors/academic")
    public List<Map<String, Object>> doctorsByAcademicData(@Valid @ModelAttribute SpecialtyInstitutionFilter filter) {
        return reportService.doctorsByAcademicData(filter);
    }

    @GetMapping("/patients/current")
    public List<Map<String, Object>> currentHospitalPatients(@Valid @ModelAttribute CurrentHospitalPatientsFilter filter) {
        return reportService.currentHospitalPatients(filter);
    }

    @GetMapping("/patients/hospitalizations")
    public List<Map<String, Object>> hospitalizedPatients(@Valid @ModelAttribute HospitalizedPatientsFilter filter) {
        return reportService.hospitalizedPatients(filter);
    }

    @GetMapping("/patients/polyclinic")
    public List<Map<String, Object>> polyclinicPatientsBySpecialty(
            @Valid @ModelAttribute PolyclinicSpecialtyPatientsFilter filter
    ) {
        return reportService.polyclinicPatientsBySpecialty(filter);
    }

    @GetMapping("/hospitals/wards")
    public List<Map<String, Object>> hospitalWardStats(@Valid @ModelAttribute HospitalWardStatsFilter filter) {
        return reportService.hospitalWardStats(filter);
    }

    @GetMapping("/polyclinics/offices")
    public List<Map<String, Object>> polyclinicOfficeVisits(@Valid @ModelAttribute PolyclinicOfficeVisitsFilter filter) {
        return reportService.polyclinicOfficeVisits(filter);
    }

    @GetMapping("/doctors/productivity")
    public List<Map<String, Object>> doctorProductivity(@Valid @ModelAttribute DoctorProductivityFilter filter) {
        return reportService.doctorProductivity(filter);
    }

    @GetMapping("/doctors/load")
    public List<Map<String, Object>> doctorLoad(@Valid @ModelAttribute DoctorLoadFilter filter) {
        return reportService.doctorLoad(filter);
    }

    @GetMapping("/patients/operations")
    public List<Map<String, Object>> patientOperations(@Valid @ModelAttribute PatientOperationsFilter filter) {
        return reportService.patientOperations(filter);
    }

    @GetMapping("/laboratory/productivity")
    public List<Map<String, Object>> laboratoryProductivity(@Valid @ModelAttribute LaboratoryProductivityFilter filter) {
        return reportService.laboratoryProductivity(filter);
    }
}

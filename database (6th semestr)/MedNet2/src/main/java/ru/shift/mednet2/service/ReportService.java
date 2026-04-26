package ru.shift.mednet2.service;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
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
import ru.shift.mednet2.repository.ReportRepository;

@Service
public class ReportService {

    private final ReportRepository reportRepository;

    public ReportService(ReportRepository reportRepository) {
        this.reportRepository = reportRepository;
    }

    public List<Map<String, Object>> doctorsBySpecialty(SpecialtyInstitutionFilter filter) {
        return reportRepository.findDoctorsBySpecialty(
                normalize(filter.getSpecialty()),
                filter.getInstitutionId(),
                normalize(filter.getInstitutionType()),
                normalize(filter.getCity())
        );
    }

    public List<Map<String, Object>> supportStaffBySpecialty(SpecialtyInstitutionFilter filter) {
        return reportRepository.findSupportStaffBySpecialty(
                normalize(filter.getSpecialty()),
                filter.getInstitutionId(),
                normalize(filter.getInstitutionType()),
                normalize(filter.getCity())
        );
    }

    public List<Map<String, Object>> doctorsByOperations(DoctorsByOperationsFilter filter) {
        return reportRepository.findDoctorsByOperations(
                normalize(filter.getSpecialty()),
                filter.getMinOperations(),
                filter.getInstitutionId(),
                normalize(filter.getInstitutionType()),
                normalize(filter.getCity())
        );
    }

    public List<Map<String, Object>> doctorsByExperience(DoctorsByExperienceFilter filter) {
        return reportRepository.findDoctorsByExperience(
                normalize(filter.getSpecialty()),
                filter.getMinExperience(),
                filter.getInstitutionId(),
                normalize(filter.getInstitutionType()),
                normalize(filter.getCity())
        );
    }

    public List<Map<String, Object>> doctorsByAcademicData(SpecialtyInstitutionFilter filter) {
        return reportRepository.findDoctorsByDegreeAndTitle(
                normalize(filter.getSpecialty()),
                filter.getInstitutionId(),
                normalize(filter.getInstitutionType()),
                normalize(filter.getCity())
        );
    }

    public List<Map<String, Object>> currentHospitalPatients(CurrentHospitalPatientsFilter filter) {
        return reportRepository.findCurrentHospitalPatients(
                filter.getHospitalId(),
                filter.getDepartmentId(),
                filter.getWardId(),
                filter.getWardNumber()
        );
    }

    public List<Map<String, Object>> hospitalizedPatients(HospitalizedPatientsFilter filter) {
        requireAnyFilter("Either hospitalId or doctorId must be provided", filter.getHospitalId(), filter.getDoctorId());
        validateDateRange(filter.getStartDate(), filter.getEndDate());
        return reportRepository.findHospitalizedPatients(
                filter.getHospitalId(),
                filter.getDoctorId(),
                filter.getStartDate(),
                filter.getEndDate()
        );
    }

    public List<Map<String, Object>> polyclinicPatientsBySpecialty(PolyclinicSpecialtyPatientsFilter filter) {
        return reportRepository.findPolyclinicPatientsByDoctorSpecialty(
                normalize(filter.getSpecialty()),
                filter.getPolyclinicId()
        );
    }

    public List<Map<String, Object>> hospitalWardStats(HospitalWardStatsFilter filter) {
        return reportRepository.findHospitalWardAndBedStats(filter.getHospitalId());
    }

    public List<Map<String, Object>> polyclinicOfficeVisits(PolyclinicOfficeVisitsFilter filter) {
        validateDateRange(filter.getStartDate(), filter.getEndDate());
        return reportRepository.findPolyclinicOfficeVisits(
                filter.getPolyclinicId(),
                filter.getStartDate(),
                filter.getEndDate()
        );
    }

    public List<Map<String, Object>> doctorProductivity(DoctorProductivityFilter filter) {
        requireAnyFilter(
                "At least one filter must be provided: doctorId, polyclinicId or specialty",
                filter.getDoctorId(),
                filter.getPolyclinicId(),
                normalize(filter.getSpecialty())
        );
        validateDateRange(filter.getStartDate(), filter.getEndDate());
        return reportRepository.findDoctorProductivity(
                filter.getStartDate(),
                filter.getEndDate(),
                filter.getDoctorId(),
                filter.getPolyclinicId(),
                normalize(filter.getSpecialty())
        );
    }

    public List<Map<String, Object>> doctorLoad(DoctorLoadFilter filter) {
        requireAnyFilter(
                "At least one filter must be provided: doctorId, hospitalId or specialty",
                filter.getDoctorId(),
                filter.getHospitalId(),
                normalize(filter.getSpecialty())
        );
        return reportRepository.findDoctorLoad(
                filter.getDoctorId(),
                filter.getHospitalId(),
                normalize(filter.getSpecialty())
        );
    }

    public List<Map<String, Object>> patientOperations(PatientOperationsFilter filter) {
        validateDateRange(filter.getStartDate(), filter.getEndDate());
        return reportRepository.findPatientsWithOperations(
                filter.getInstitutionId(),
                normalize(filter.getInstitutionType()),
                filter.getDoctorId(),
                filter.getStartDate(),
                filter.getEndDate()
        );
    }

    public List<Map<String, Object>> laboratoryProductivity(LaboratoryProductivityFilter filter) {
        validateDateRange(filter.getStartDate(), filter.getEndDate());
        return reportRepository.findLaboratoryProductivity(
                filter.getInstitutionId(),
                normalize(filter.getCity()),
                filter.getStartDate(),
                filter.getEndDate()
        );
    }

    private void validateDateRange(LocalDate startDate, LocalDate endDate) {
        if (endDate.isBefore(startDate)) {
            throw new IllegalArgumentException("endDate must be greater than or equal to startDate");
        }
    }

    private void requireAnyFilter(String message, Object... values) {
        for (Object value : values) {
            if (value != null) {
                return;
            }
        }
        throw new IllegalArgumentException(message);
    }

    private String normalize(String value) {
        if (value == null) {
            return null;
        }
        String normalized = value.trim();
        return normalized.isEmpty() ? null : normalized;
    }
}

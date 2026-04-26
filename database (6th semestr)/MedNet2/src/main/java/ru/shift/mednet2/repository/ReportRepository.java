package ru.shift.mednet2.repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class ReportRepository {

    private final NamedParameterJdbcTemplate jdbcTemplate;

    public ReportRepository(NamedParameterJdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<Map<String, Object>> findDoctorsBySpecialty(
            String specialtyName,
            Integer institutionId,
            String institutionType,
            String city
    ) {
        var params = new MapSqlParameterSource()
                .addValue("specialty_name", specialtyName)
                .addValue("institution_id", institutionId)
                .addValue("institution_type", institutionType)
                .addValue("city", city);
        return jdbcTemplate.queryForList(QUERY_1, params);
    }

    public List<Map<String, Object>> findSupportStaffBySpecialty(
            String specialtyName,
            Integer institutionId,
            String institutionType,
            String city
    ) {
        var params = new MapSqlParameterSource()
                .addValue("specialty_name", specialtyName)
                .addValue("institution_id", institutionId)
                .addValue("institution_type", institutionType)
                .addValue("city", city);
        return jdbcTemplate.queryForList(QUERY_2, params);
    }

    public List<Map<String, Object>> findDoctorsByOperations(
            String specialtyName,
            int minOperations,
            Integer institutionId,
            String institutionType,
            String city
    ) {
        var params = new MapSqlParameterSource()
                .addValue("specialty_name", specialtyName)
                .addValue("min_operations", minOperations)
                .addValue("institution_id", institutionId)
                .addValue("institution_type", institutionType)
                .addValue("city", city);
        return jdbcTemplate.queryForList(QUERY_3, params);
    }

    public List<Map<String, Object>> findDoctorsByExperience(
            String specialtyName,
            int minExperience,
            Integer institutionId,
            String institutionType,
            String city
    ) {
        var params = new MapSqlParameterSource()
                .addValue("specialty_name", specialtyName)
                .addValue("min_experience", minExperience)
                .addValue("institution_id", institutionId)
                .addValue("institution_type", institutionType)
                .addValue("city", city);
        return jdbcTemplate.queryForList(QUERY_4, params);
    }

    public List<Map<String, Object>> findDoctorsByDegreeAndTitle(
            String specialtyName,
            Integer institutionId,
            String institutionType,
            String city
    ) {
        var params = new MapSqlParameterSource()
                .addValue("specialty_name", specialtyName)
                .addValue("institution_id", institutionId)
                .addValue("institution_type", institutionType)
                .addValue("city", city);
        return jdbcTemplate.queryForList(QUERY_5, params);
    }

    public List<Map<String, Object>> findCurrentHospitalPatients(
            int hospitalId,
            Integer departmentId,
            Integer wardId,
            Integer wardNumber
    ) {
        var params = new MapSqlParameterSource()
                .addValue("hospital_id", hospitalId)
                .addValue("department_id", departmentId)
                .addValue("ward_id", wardId)
                .addValue("ward_number", wardNumber);
        return jdbcTemplate.queryForList(QUERY_6, params);
    }

    public List<Map<String, Object>> findHospitalizedPatients(
            Integer hospitalId,
            Integer doctorId,
            LocalDate startDate,
            LocalDate endDate
    ) {
        var params = new MapSqlParameterSource()
                .addValue("hospital_id", hospitalId)
                .addValue("doctor_id", doctorId)
                .addValue("start_date", startDate)
                .addValue("end_date", endDate);
        return jdbcTemplate.queryForList(QUERY_7, params);
    }

    public List<Map<String, Object>> findPolyclinicPatientsByDoctorSpecialty(
            String specialtyName,
            int polyclinicId
    ) {
        var params = new MapSqlParameterSource()
                .addValue("specialty_name", specialtyName)
                .addValue("polyclinic_id", polyclinicId);
        return jdbcTemplate.queryForList(QUERY_8, params);
    }

    public List<Map<String, Object>> findHospitalWardAndBedStats(int hospitalId) {
        var params = new MapSqlParameterSource().addValue("hospital_id", hospitalId);
        return jdbcTemplate.queryForList(QUERY_9, params);
    }

    public List<Map<String, Object>> findPolyclinicOfficeVisits(
            int polyclinicId,
            LocalDate startDate,
            LocalDate endDate
    ) {
        var params = new MapSqlParameterSource()
                .addValue("polyclinic_id", polyclinicId)
                .addValue("start_date", startDate)
                .addValue("end_date", endDate);
        return jdbcTemplate.queryForList(QUERY_10, params);
    }

    public List<Map<String, Object>> findDoctorProductivity(
            LocalDate startDate,
            LocalDate endDate,
            Integer doctorId,
            Integer polyclinicId,
            String specialtyName
    ) {
        var params = new MapSqlParameterSource()
                .addValue("start_date", startDate)
                .addValue("end_date", endDate)
                .addValue("doctor_id", doctorId)
                .addValue("polyclinic_id", polyclinicId)
                .addValue("specialty_name", specialtyName);
        return jdbcTemplate.queryForList(QUERY_11, params);
    }

    public List<Map<String, Object>> findDoctorLoad(
            Integer doctorId,
            Integer hospitalId,
            String specialtyName
    ) {
        var params = new MapSqlParameterSource()
                .addValue("doctor_id", doctorId)
                .addValue("hospital_id", hospitalId)
                .addValue("specialty_name", specialtyName);
        return jdbcTemplate.queryForList(QUERY_12, params);
    }

    public List<Map<String, Object>> findPatientsWithOperations(
            Integer institutionId,
            String institutionType,
            Integer doctorId,
            LocalDate startDate,
            LocalDate endDate
    ) {
        var params = new MapSqlParameterSource()
                .addValue("institution_id", institutionId)
                .addValue("institution_type", institutionType)
                .addValue("doctor_id", doctorId)
                .addValue("start_date", startDate)
                .addValue("end_date", endDate);
        return jdbcTemplate.queryForList(QUERY_13, params);
    }

    public List<Map<String, Object>> findLaboratoryProductivity(
            Integer institutionId,
            String city,
            LocalDate startDate,
            LocalDate endDate
    ) {
        var params = new MapSqlParameterSource()
                .addValue("institution_id", institutionId)
                .addValue("city", city)
                .addValue("start_date", startDate)
                .addValue("end_date", endDate);
        return jdbcTemplate.queryForList(QUERY_14, params);
    }

    private static final String QUERY_1 = """
            WITH current_employment AS (
                SELECT EmployeeID, InstitutionID
                FROM Employment
                WHERE EndDate IS NULL OR EndDate >= CURRENT_DATE
            ),
            filtered_doctors AS (
                SELECT DISTINCT d.DoctorID, e.FullName, s.Name AS SpecialtyName
                FROM Doctors d
                JOIN Employees e ON d.DoctorID = e.EmployeeID
                JOIN Specialties s ON d.SpecialtyID = s.SpecialtyID
                JOIN current_employment ce ON d.DoctorID = ce.EmployeeID
                JOIN MedicalInstitutions mi ON ce.InstitutionID = mi.InstitutionID
                WHERE s.Name = :specialty_name
                  AND (CAST(:institution_id AS INTEGER) IS NULL OR mi.InstitutionID = :institution_id)
                  AND (CAST(:institution_type AS VARCHAR) IS NULL OR mi.Type = :institution_type)
                  AND (CAST(:city AS VARCHAR) IS NULL OR mi.Address LIKE '%%' || :city || '%%')
            )
            SELECT
                DoctorID,
                FullName,
                SpecialtyName,
                COUNT(*) OVER() AS total_doctors
            FROM filtered_doctors
            ORDER BY FullName
            """;

    private static final String QUERY_2 = """
            WITH filtered_staff AS (
                SELECT DISTINCT
                    e.EmployeeID,
                    e.FullName,
                    ss.Specialty,
                    mi.Name AS InstitutionName,
                    mi.Type AS InstitutionType
                FROM SupportStaff ss
                JOIN Employees e ON ss.StaffID = e.EmployeeID
                JOIN Employment t ON e.EmployeeID = t.EmployeeID
                JOIN MedicalInstitutions mi ON t.InstitutionID = mi.InstitutionID
                WHERE ss.Specialty = :specialty_name
                  AND (t.EndDate IS NULL OR t.EndDate > CURRENT_DATE)
                  AND (CAST(:institution_id AS INTEGER) IS NULL OR mi.InstitutionID = :institution_id)
                  AND (CAST(:institution_type AS VARCHAR) IS NULL OR mi.Type = :institution_type)
                  AND (CAST(:city AS VARCHAR) IS NULL OR mi.Address LIKE '%%' || :city || '%%')
            )
            SELECT
                fs.FullName AS "ФИО",
                fs.Specialty AS "Специальность",
                fs.InstitutionName AS "Учреждение",
                fs.InstitutionType AS "Тип",
                (SELECT COUNT(DISTINCT EmployeeID) FROM filtered_staff) AS "Общее_число_сотрудников"
            FROM filtered_staff fs
            ORDER BY fs.InstitutionName, fs.FullName
            """;

    private static final String QUERY_3 = """
            WITH doctor_operations AS (
                SELECT
                    d.DoctorID,
                    e.FullName,
                    s.Name AS "Специальность",
                    COUNT(op.OperationID) AS "Количество_операций",
                    STRING_AGG(DISTINCT mi.Name, '; ') AS "Учреждения"
                FROM Doctors d
                JOIN Employees e ON d.DoctorID = e.EmployeeID
                JOIN Specialties s ON d.SpecialtyID = s.SpecialtyID
                JOIN Employment emp ON d.DoctorID = emp.EmployeeID
                JOIN MedicalInstitutions mi ON emp.InstitutionID = mi.InstitutionID
                LEFT JOIN Operations op
                    ON d.DoctorID = op.DoctorID
                   AND op.PerformedDate BETWEEN emp.StartDate
                                        AND COALESCE(emp.EndDate, DATE '9999-12-31')
                WHERE s.Name = :specialty_name
                  AND (emp.EndDate IS NULL OR emp.EndDate >= CURRENT_DATE)
                  AND (CAST(:institution_id AS INTEGER) IS NULL OR mi.InstitutionID = :institution_id)
                  AND (CAST(:institution_type AS VARCHAR) IS NULL OR mi.Type = :institution_type)
                  AND (CAST(:city AS VARCHAR) IS NULL OR mi.Address ILIKE '%%' || :city || '%%')
                GROUP BY d.DoctorID, e.FullName, s.Name
                HAVING COUNT(op.OperationID) >= :min_operations
            )
            SELECT
                DoctorID,
                FullName AS "ФИО",
                "Специальность",
                "Количество_операций",
                "Учреждения",
                COUNT(*) OVER() AS "Общее_число_врачей"
            FROM doctor_operations
            ORDER BY FullName
            """;

    private static final String QUERY_4 = """
            WITH current_employment AS (
                SELECT
                    emp.EmployeeID,
                    emp.InstitutionID,
                    mi.Name AS InstitutionName,
                    mi.Type AS InstitutionType,
                    mi.Address,
                    EXTRACT(YEAR FROM AGE(CURRENT_DATE, emp.StartDate)) AS experience_years
                FROM Employment emp
                JOIN MedicalInstitutions mi ON emp.InstitutionID = mi.InstitutionID
                WHERE emp.EndDate IS NULL OR emp.EndDate >= CURRENT_DATE
            )
            SELECT
                d.DoctorID,
                e.FullName AS "ФИО",
                s.Name AS "Специальность",
                ce.InstitutionName AS "Учреждение",
                ce.InstitutionType AS "Тип",
                ce.experience_years AS "Стаж_лет",
                COUNT(*) OVER() AS "Общее_число_врачей"
            FROM Doctors d
            JOIN Employees e ON d.DoctorID = e.EmployeeID
            JOIN Specialties s ON d.SpecialtyID = s.SpecialtyID
            JOIN current_employment ce ON d.DoctorID = ce.EmployeeID
            WHERE s.Name = :specialty_name
              AND ce.experience_years >= :min_experience
              AND (CAST(:institution_id AS INTEGER) IS NULL OR ce.InstitutionID = :institution_id)
              AND (CAST(:institution_type AS VARCHAR) IS NULL OR ce.InstitutionType = :institution_type)
              AND (CAST(:city AS VARCHAR) IS NULL OR ce.Address LIKE '%%' || :city || '%%')
            ORDER BY ce.InstitutionName, e.FullName
            """;

    private static final String QUERY_5 = """
            WITH current_employment AS (
                SELECT DISTINCT EmployeeID, InstitutionID
                FROM Employment
                WHERE EndDate IS NULL OR EndDate > CURRENT_DATE
            )
            SELECT
                d.DoctorID,
                e.FullName AS "ФИО",
                s.Name AS "Специальность",
                d.Degree AS "Ученая_степень",
                d.Title AS "Ученое_звание",
                mi.Name AS "Учреждение",
                mi.Type AS "Тип",
                COUNT(*) OVER() AS "Общее_число_врачей"
            FROM Doctors d
            JOIN Employees e ON d.DoctorID = e.EmployeeID
            JOIN Specialties s ON d.SpecialtyID = s.SpecialtyID
            JOIN current_employment ce ON d.DoctorID = ce.EmployeeID
            JOIN MedicalInstitutions mi ON ce.InstitutionID = mi.InstitutionID
            WHERE s.Name = :specialty_name
              AND d.Degree IN ('кандидат', 'доктор')
              AND d.Title IN ('доцент', 'профессор')
              AND (CAST(:institution_id AS INTEGER) IS NULL OR mi.InstitutionID = :institution_id)
              AND (CAST(:institution_type AS VARCHAR) IS NULL OR mi.Type = :institution_type)
              AND (CAST(:city AS VARCHAR) IS NULL OR mi.Address LIKE '%%' || :city || '%%')
            ORDER BY mi.Name, e.FullName
            """;

    private static final String QUERY_6 = """
            WITH filtered_beds AS (
                SELECT b.BedID
                FROM Beds b
                JOIN Wards w ON b.WardID = w.WardID
                JOIN Departments d ON w.DepartmentID = d.DepartmentID
                JOIN Hospitals h ON d.HospitalID = h.HospitalID
                WHERE h.HospitalID = :hospital_id
                  AND (CAST(:department_id AS INTEGER) IS NULL OR d.DepartmentID = :department_id)
                  AND (CAST(:ward_id AS INTEGER) IS NULL OR w.WardID = :ward_id)
                  AND (CAST(:ward_number AS INTEGER) IS NULL OR w.Number = :ward_number)
            )
            SELECT
                p.PatientID,
                p.FullName AS "ФИО_пациента",
                p.BirthDate AS "Дата_рождения",
                p.OMSNumber AS "Номер_полиса",
                p.PhoneNumber AS "Телефон",
                pj.AdmissionDate AS "Дата_поступления",
                CASE
                    WHEN pj.DischargeDate IS NULL THEN 'На лечении'
                    ELSE 'Выписан'
                END AS "Состояние",
                NULL AS "Температура",
                (
                    SELECT e.FullName
                    FROM Operations op
                    JOIN Doctors doc ON op.DoctorID = doc.DoctorID
                    JOIN Employees e ON doc.DoctorID = e.EmployeeID
                    WHERE op.PatientID = p.PatientID
                      AND op.PerformedDate <= CURRENT_DATE
                    ORDER BY op.PerformedDate DESC
                    LIMIT 1
                ) AS "Лечащий_врач",
                b.Number AS "Номер_койки",
                w.Number AS "Номер_палаты",
                d.Name AS "Отделение",
                COUNT(*) OVER() AS "Общее_число_пациентов"
            FROM PlacementJournal pj
            JOIN Patients p ON pj.PatientID = p.PatientID
            JOIN Beds b ON pj.BedID = b.BedID
            JOIN Wards w ON b.WardID = w.WardID
            JOIN Departments d ON w.DepartmentID = d.DepartmentID
            WHERE pj.DischargeDate IS NULL
              AND pj.BedID IN (SELECT BedID FROM filtered_beds)
            ORDER BY d.Name, w.Number, p.FullName
            """;

    private static final String QUERY_7 = """
            WITH hospital_patients AS (
                SELECT DISTINCT
                    p.PatientID,
                    p.FullName,
                    p.BirthDate,
                    p.OMSNumber,
                    p.PhoneNumber,
                    pj.AdmissionDate AS "Дата_поступления",
                    pj.DischargeDate AS "Дата_выписки",
                    d.Name AS "Отделение",
                    w.Number AS "Палата",
                    b.Number AS "Койка",
                    (
                        SELECT e.FullName
                        FROM Operations op
                        JOIN Doctors d2 ON op.DoctorID = d2.DoctorID
                        JOIN Employees e ON d2.DoctorID = e.EmployeeID
                        WHERE op.PatientID = p.PatientID
                          AND op.PerformedDate BETWEEN pj.AdmissionDate AND COALESCE(pj.DischargeDate, CURRENT_DATE)
                        ORDER BY op.PerformedDate DESC
                        LIMIT 1
                    ) AS "Лечащий_врач",
                    'стационар' AS "Тип_лечения"
                FROM PlacementJournal pj
                JOIN Patients p ON pj.PatientID = p.PatientID
                JOIN Beds b ON pj.BedID = b.BedID
                JOIN Wards w ON b.WardID = w.WardID
                JOIN Departments d ON w.DepartmentID = d.DepartmentID
                JOIN Hospitals h ON d.HospitalID = h.HospitalID
                WHERE (CAST(:hospital_id AS INTEGER) IS NULL OR h.HospitalID = :hospital_id)
                  AND pj.AdmissionDate <= :end_date
                  AND (pj.DischargeDate IS NULL OR pj.DischargeDate >= :start_date)
                  AND (CAST(:doctor_id AS INTEGER) IS NULL OR EXISTS (
                      SELECT 1
                      FROM Operations op
                      WHERE op.PatientID = p.PatientID
                        AND op.DoctorID = :doctor_id
                        AND op.PerformedDate BETWEEN pj.AdmissionDate AND COALESCE(pj.DischargeDate, CURRENT_DATE)
                  ))
            )
            SELECT
                PatientID,
                FullName AS "ФИО_пациента",
                BirthDate AS "Дата_рождения",
                OMSNumber AS "Номер_полиса",
                PhoneNumber AS "Телефон",
                "Дата_поступления",
                "Дата_выписки",
                "Лечащий_врач",
                "Отделение",
                "Палата",
                "Койка",
                "Тип_лечения",
                COUNT(*) OVER() AS "Общее_число_пациентов"
            FROM hospital_patients
            ORDER BY "Дата_поступления" DESC, FullName
            """;

    private static final String QUERY_8 = """
            WITH polyclinic_visits AS (
                SELECT DISTINCT
                    vj.DoctorID,
                    e.FullName AS DoctorName,
                    vj.PatientID,
                    COUNT(vj.VisitID) AS "Количество_обращений",
                    MAX(vj.VisitDate) AS "Последний_визит"
                FROM VisitJournal vj
                JOIN Doctors d ON vj.DoctorID = d.DoctorID
                JOIN Employees e ON d.DoctorID = e.EmployeeID
                JOIN Specialties s ON d.SpecialtyID = s.SpecialtyID
                JOIN Offices o ON vj.OfficeID = o.OfficeID
                WHERE s.Name = :specialty_name
                  AND o.PolyclinicID = :polyclinic_id
                  AND vj.VisitDate <= CURRENT_DATE
                GROUP BY vj.DoctorID, e.FullName, vj.PatientID
            )
            SELECT
                p.PatientID,
                p.FullName AS "ФИО_пациента",
                p.BirthDate AS "Дата_рождения",
                p.OMSNumber AS "Номер_полиса",
                p.SNILS AS "СНИЛС",
                p.PhoneNumber AS "Телефон",
                p.Address AS "Адрес",
                pv.DoctorName AS "Врач",
                :specialty_name AS "Специальность_врача",
                mi.Name AS "Поликлиника",
                pv."Количество_обращений",
                pv."Последний_визит",
                COUNT(*) OVER() AS "Общее_число_пациентов"
            FROM Patients p
            JOIN MedicalInstitutions mi ON p.PolyclinicID = mi.InstitutionID
            JOIN polyclinic_visits pv ON p.PatientID = pv.PatientID
            WHERE p.PolyclinicID = :polyclinic_id
            ORDER BY pv.DoctorName, p.FullName
            """;

    private static final String QUERY_9 = """
            WITH wards_stats AS (
                SELECT
                    w.WardID,
                    w.Number AS "Номер_палаты",
                    w.DepartmentID,
                    d.Name AS "Отделение",
                    COUNT(b.BedID) AS "Всего_коек_в_палате",
                    SUM(CASE WHEN b.Status = 'free' THEN 1 ELSE 0 END) AS "Свободных_коек_в_палате",
                    CASE
                        WHEN COUNT(b.BedID) = SUM(CASE WHEN b.Status = 'free' THEN 1 ELSE 0 END)
                        THEN 1
                        ELSE 0
                    END AS "Палата_полностью_свободна"
                FROM Wards w
                JOIN Departments d ON w.DepartmentID = d.DepartmentID
                LEFT JOIN Beds b ON w.WardID = b.WardID
                WHERE d.HospitalID = :hospital_id
                GROUP BY w.WardID, w.Number, w.DepartmentID, d.Name
            ),
            department_stats AS (
                SELECT
                    DepartmentID,
                    "Отделение",
                    COUNT(DISTINCT WardID) AS "Всего_палат_в_отделении",
                    SUM("Всего_коек_в_палате") AS "Всего_коек_в_отделении",
                    SUM("Свободных_коек_в_палате") AS "Свободных_коек_в_отделении",
                    SUM("Палата_полностью_свободна") AS "Полностью_свободных_палат_в_отделении"
                FROM wards_stats
                GROUP BY DepartmentID, "Отделение"
            )
            SELECT
                result.DepartmentID,
                result."Отделение",
                result."Всего_палат_в_отделении",
                result."Всего_коек_в_отделении",
                result."Свободных_коек_в_отделении",
                result."Полностью_свободных_палат_в_отделении"
            FROM (
                SELECT
                    DepartmentID,
                    "Отделение",
                    "Всего_палат_в_отделении",
                    "Всего_коек_в_отделении",
                    "Свободных_коек_в_отделении",
                    "Полностью_свободных_палат_в_отделении",
                    0 AS sort_order
                FROM department_stats
                UNION ALL
                SELECT
                    NULL AS DepartmentID,
                    'ВСЕГО ПО БОЛЬНИЦЕ' AS "Отделение",
                    SUM("Всего_палат_в_отделении") AS "Всего_палат_в_отделении",
                    SUM("Всего_коек_в_отделении") AS "Всего_коек_в_отделении",
                    SUM("Свободных_коек_в_отделении") AS "Свободных_коек_в_отделении",
                    SUM("Полностью_свободных_палат_в_отделении") AS "Полностью_свободных_палат_в_отделении",
                    1 AS sort_order
                FROM department_stats
            ) result
            ORDER BY result.sort_order, result.DepartmentID
            """;

    private static final String QUERY_10 = """
            WITH office_stats AS (
                SELECT
                    o.OfficeID,
                    o.Number AS nomer_kabineta,
                    COUNT(vj.VisitID) AS chislo_poseshcheniy
                FROM Offices o
                LEFT JOIN VisitJournal vj ON o.OfficeID = vj.OfficeID
                    AND vj.VisitDate BETWEEN :start_date AND :end_date
                WHERE o.PolyclinicID = :polyclinic_id
                GROUP BY o.OfficeID, o.Number
            )
            SELECT
                office_stats.OfficeID,
                office_stats.nomer_kabineta,
                office_stats.chislo_poseshcheniy,
                COUNT(*) OVER() AS obshee_chislo_kabinetov,
                SUM(office_stats.chislo_poseshcheniy) OVER() AS vsego_poseshcheniy_za_period
            FROM office_stats
            ORDER BY office_stats.nomer_kabineta
            """;

    private static final String QUERY_11 = """
            WITH days_in_period AS (
                SELECT (CAST(:end_date AS DATE) - CAST(:start_date AS DATE)) + 1 AS total_days
            ),
            doctor_visits AS (
                SELECT
                    d.DoctorID,
                    e.FullName AS doctor_name,
                    s.Name AS specialty,
                    mi.Name AS polyclinic_name,
                    COUNT(vj.VisitID) AS total_visits,
                    COUNT(DISTINCT vj.VisitDate) AS working_days_with_patients
                FROM Doctors d
                JOIN Employees e ON d.DoctorID = e.EmployeeID
                JOIN Specialties s ON d.SpecialtyID = s.SpecialtyID
                JOIN Employment emp ON d.DoctorID = emp.EmployeeID
                JOIN MedicalInstitutions mi ON emp.InstitutionID = mi.InstitutionID
                LEFT JOIN VisitJournal vj ON d.DoctorID = vj.DoctorID
                    AND vj.VisitDate BETWEEN :start_date AND :end_date
                WHERE mi.Type = 'Polyclinic'
                  AND (emp.EndDate IS NULL OR emp.EndDate >= CURRENT_DATE)
                  AND (CAST(:doctor_id AS INTEGER) IS NULL OR d.DoctorID = :doctor_id)
                  AND (CAST(:polyclinic_id AS INTEGER) IS NULL OR mi.InstitutionID = :polyclinic_id)
                  AND (CAST(:specialty_name AS VARCHAR) IS NULL OR s.Name = :specialty_name)
                GROUP BY d.DoctorID, e.FullName, s.Name, mi.Name
            )
            SELECT
                dv.DoctorID,
                dv.doctor_name AS "ФИО_врача",
                dv.specialty AS "Специальность",
                dv.polyclinic_name AS "Поликлиника",
                dv.total_visits AS "Всего_пациентов_за_период",
                ROUND(CAST(dv.total_visits AS NUMERIC) / dp.total_days, 2) AS "Среднее_пациентов_в_день",
                ROUND(CAST(dv.total_visits AS NUMERIC) / NULLIF(dv.working_days_with_patients, 0), 2) AS "Среднее_в_рабочий_день",
                dv.working_days_with_patients AS "Дней_с_приемами",
                dp.total_days AS "Дней_в_периоде",
                COUNT(*) OVER() AS "Всего_врачей_в_выборке"
            FROM doctor_visits dv
            CROSS JOIN days_in_period dp
            WHERE dv.total_visits > 0 OR CAST(:doctor_id AS INTEGER) IS NOT NULL
            ORDER BY dv.specialty, dv.doctor_name
            """;

    private static final String QUERY_12 = """
            WITH current_patients AS (
                SELECT
                    pj.PatientID,
                    (
                        SELECT op.DoctorID
                        FROM Operations op
                        WHERE op.PatientID = pj.PatientID
                          AND op.PerformedDate <= CURRENT_DATE
                        ORDER BY op.PerformedDate DESC
                        LIMIT 1
                    ) AS DoctorID
                FROM PlacementJournal pj
                WHERE pj.DischargeDate IS NULL
            ),
            doctor_load AS (
                SELECT
                    cp.DoctorID,
                    COUNT(cp.PatientID) AS tekushchih_patsientov
                FROM current_patients cp
                WHERE cp.DoctorID IS NOT NULL
                GROUP BY cp.DoctorID
            ),
            filtered_doctors AS (
                SELECT DISTINCT
                    d.DoctorID,
                    e.FullName AS doctor_name,
                    s.Name AS specialty,
                    mi.InstitutionID,
                    mi.Name AS hospital_name
                FROM Doctors d
                JOIN Employees e ON d.DoctorID = e.EmployeeID
                JOIN Specialties s ON d.SpecialtyID = s.SpecialtyID
                JOIN Employment emp ON d.DoctorID = emp.EmployeeID
                JOIN MedicalInstitutions mi ON emp.InstitutionID = mi.InstitutionID
                WHERE mi.Type = 'Hospital'
                  AND (emp.EndDate IS NULL OR emp.EndDate > CURRENT_DATE)
                  AND (CAST(:doctor_id AS INTEGER) IS NULL OR d.DoctorID = :doctor_id)
                  AND (CAST(:hospital_id AS INTEGER) IS NULL OR mi.InstitutionID = :hospital_id)
                  AND (CAST(:specialty_name AS VARCHAR) IS NULL OR s.Name = :specialty_name)
            )
            SELECT
                fd.doctor_name AS "ФИО_врача",
                fd.specialty AS "Специальность",
                fd.hospital_name AS "Больница",
                COALESCE(dl.tekushchih_patsientov, 0) AS "Текущих_пациентов",
                CASE
                    WHEN COALESCE(dl.tekushchih_patsientov, 0) = 0 THEN 'Нет пациентов'
                    WHEN COALESCE(dl.tekushchih_patsientov, 0) <= 3 THEN 'Низкая загрузка'
                    WHEN COALESCE(dl.tekushchih_patsientov, 0) <= 7 THEN 'Средняя загрузка'
                    ELSE 'Высокая загрузка'
                END AS "Уровень_загрузки",
                COUNT(*) OVER() AS "Всего_врачей_в_выборке",
                SUM(COALESCE(dl.tekushchih_patsientov, 0)) OVER() AS "Всего_пациентов_по_всем_врачам"
            FROM filtered_doctors fd
            LEFT JOIN doctor_load dl ON fd.DoctorID = dl.DoctorID
            ORDER BY fd.specialty, fd.doctor_name
            """;

    private static final String QUERY_13 = """
            WITH filtered_operations AS (
                SELECT
                    op.OperationID,
                    op.PatientID,
                    op.DoctorID,
                    op.TypeID,
                    op.PerformedDate,
                    op.Outcome,
                    op.Description,
                    (
                        SELECT emp.InstitutionID
                        FROM Employment emp
                        WHERE emp.EmployeeID = op.DoctorID
                          AND emp.StartDate <= op.PerformedDate
                          AND (emp.EndDate IS NULL OR emp.EndDate >= op.PerformedDate)
                        LIMIT 1
                    ) AS InstitutionID
                FROM Operations op
                WHERE op.PerformedDate BETWEEN :start_date AND :end_date
            ),
            operation_rows AS (
                SELECT
                    p.PatientID,
                    p.FullName AS "ФИО_пациента",
                    p.BirthDate AS "Дата_рождения",
                    p.OMSNumber AS "Номер_полиса",
                    p.PhoneNumber AS "Телефон",
                    e.FullName AS "Врач",
                    s.Name AS "Специальность_врача",
                    ot.Name AS "Тип_операции",
                    fo.PerformedDate AS "Дата_операции",
                    fo.Outcome AS "Исход",
                    fo.Description AS "Описание",
                    mi.Name AS "Учреждение",
                    mi.Type AS "Тип_учреждения"
                FROM filtered_operations fo
                JOIN Patients p ON fo.PatientID = p.PatientID
                JOIN Doctors d ON fo.DoctorID = d.DoctorID
                JOIN Employees e ON d.DoctorID = e.EmployeeID
                JOIN Specialties s ON d.SpecialtyID = s.SpecialtyID
                JOIN OperationTypes ot ON fo.TypeID = ot.TypeID
                LEFT JOIN MedicalInstitutions mi ON fo.InstitutionID = mi.InstitutionID
                WHERE (CAST(:institution_id AS INTEGER) IS NULL OR fo.InstitutionID = :institution_id)
                  AND (CAST(:institution_type AS VARCHAR) IS NULL OR mi.Type = :institution_type)
                  AND (CAST(:doctor_id AS INTEGER) IS NULL OR fo.DoctorID = :doctor_id)
            ),
            totals AS (
                SELECT
                    COUNT(*) AS total_operations,
                    COUNT(DISTINCT PatientID) AS total_patients
                FROM operation_rows
            )
            SELECT
                operation_rows.*,
                totals.total_operations AS "Общее_число_операций",
                totals.total_patients AS "Общее_число_пациентов"
            FROM operation_rows
            CROSS JOIN totals
            ORDER BY operation_rows."Дата_операции" DESC, operation_rows."ФИО_пациента"
            """;

    private static final String QUERY_14 = """
            WITH days_in_period AS (
                SELECT (CAST(:end_date AS DATE) - CAST(:start_date AS DATE)) + 1 AS total_days
            ),
            laboratory_services AS (
                SELECT
                    mi.InstitutionID,
                    mi.Name AS laboratory_name,
                    mi.Address,
                    ms.ServiceID,
                    ms.ServiceDate,
                    ms.ServiceType,
                    ms.EmployeeID,
                    ms.Results
                FROM MedicalServices ms
                JOIN Employees e ON ms.EmployeeID = e.EmployeeID
                JOIN Employment emp ON e.EmployeeID = emp.EmployeeID
                JOIN MedicalInstitutions mi ON emp.InstitutionID = mi.InstitutionID
                WHERE mi.Type = 'Laboratory'
                  AND ms.ServiceDate BETWEEN :start_date AND :end_date
                  AND (emp.EndDate IS NULL OR emp.EndDate >= ms.ServiceDate)
                  AND (CAST(:institution_id AS INTEGER) IS NULL OR mi.InstitutionID = :institution_id)
                  AND (CAST(:city AS VARCHAR) IS NULL OR mi.Address LIKE '%%' || :city || '%%')
            ),
            lab_stats AS (
                SELECT
                    InstitutionID,
                    laboratory_name,
                    Address,
                    COUNT(ServiceID) AS vsego_obsledovaniy,
                    COUNT(DISTINCT ServiceDate) AS dney_s_obsledovaniyami,
                    MIN(ServiceDate) AS pervoe_obsledovanie,
                    MAX(ServiceDate) AS poslednee_obsledovanie,
                    COUNT(DISTINCT EmployeeID) AS chislo_sotrudnikov,
                    COUNT(DISTINCT ServiceType) AS razlichnyh_tipov_obsledovaniy
                FROM laboratory_services
                GROUP BY InstitutionID, laboratory_name, Address
            )
            SELECT
                lab_stats.InstitutionID,
                lab_stats.laboratory_name AS "Лаборатория",
                lab_stats.Address AS "Адрес",
                lab_stats.vsego_obsledovaniy AS "Всего_обследований_за_период",
                lab_stats.dney_s_obsledovaniyami AS "Дней_с_обследованиями",
                ROUND(CAST(lab_stats.vsego_obsledovaniy AS NUMERIC) / dp.total_days, 2) AS "Среднее_в_день",
                CASE
                    WHEN lab_stats.dney_s_obsledovaniyami > 0
                    THEN ROUND(CAST(lab_stats.vsego_obsledovaniy AS NUMERIC) / lab_stats.dney_s_obsledovaniyami, 2)
                    ELSE 0
                END AS "Среднее_в_рабочий_день",
                lab_stats.chislo_sotrudnikov AS "Задействовано_сотрудников",
                lab_stats.razlichnyh_tipov_obsledovaniy AS "Типов_обследований",
                lab_stats.pervoe_obsledovanie AS "Первое_обследование",
                lab_stats.poslednee_obsledovanie AS "Последнее_обследование",
                dp.total_days AS "Дней_в_периоде",
                COUNT(*) OVER() AS "Всего_лабораторий_в_выборке",
                SUM(lab_stats.vsego_obsledovaniy) OVER() AS "Всего_обследований_по_всем_лабораториям"
            FROM lab_stats
            CROSS JOIN days_in_period dp
            ORDER BY lab_stats.laboratory_name
            """;
}

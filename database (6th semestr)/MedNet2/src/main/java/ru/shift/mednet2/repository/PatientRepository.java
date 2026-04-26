package ru.shift.mednet2.repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;
import ru.shift.mednet2.dto.PatientDto;

@Repository
public class PatientRepository {

    private final JdbcTemplate jdbcTemplate;

    public PatientRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<PatientDto> findAll() {
        String sql = """
                SELECT PatientID, FullName, BirthDate, Address, PolyclinicID, OMSNumber, SNILS, PassportData, PhoneNumber
                FROM Patients
                ORDER BY FullName
                """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> mapRow(rs));
    }

    public Optional<PatientDto> findById(int id) {
        String sql = """
                SELECT PatientID, FullName, BirthDate, Address, PolyclinicID, OMSNumber, SNILS, PassportData, PhoneNumber
                FROM Patients
                WHERE PatientID = ?
                """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> mapRow(rs), id).stream().findFirst();
    }

    public List<PatientDto> findByPolyclinicId(int polyclinicId) {
        String sql = """
                SELECT PatientID, FullName, BirthDate, Address, PolyclinicID, OMSNumber, SNILS, PassportData, PhoneNumber
                FROM Patients
                WHERE PolyclinicID = ?
                ORDER BY FullName
                """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> mapRow(rs), polyclinicId);
    }

    public PatientDto create(PatientDto dto) {
        int id = nextId();
        String sql = """
                INSERT INTO Patients (PatientID, FullName, BirthDate, Address, PolyclinicID, OMSNumber, SNILS, PassportData, PhoneNumber)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """;
        jdbcTemplate.update(
                sql,
                id,
                dto.getFullName(),
                dto.getBirthDate(),
                dto.getAddress(),
                dto.getPolyclinicId(),
                dto.getOmsNumber(),
                dto.getSnils(),
                dto.getPassportData(),
                dto.getPhoneNumber()
        );
        dto.setPatientId(id);
        return dto;
    }

    public boolean update(PatientDto dto) {
        String sql = """
                UPDATE Patients
                SET FullName = ?, BirthDate = ?, Address = ?, PolyclinicID = ?, OMSNumber = ?, SNILS = ?, PassportData = ?, PhoneNumber = ?
                WHERE PatientID = ?
                """;
        return jdbcTemplate.update(
                sql,
                dto.getFullName(),
                dto.getBirthDate(),
                dto.getAddress(),
                dto.getPolyclinicId(),
                dto.getOmsNumber(),
                dto.getSnils(),
                dto.getPassportData(),
                dto.getPhoneNumber(),
                dto.getPatientId()
        ) > 0;
    }

    public boolean deleteById(int id) {
        String sql = "DELETE FROM Patients WHERE PatientID = ?";
        return jdbcTemplate.update(sql, id) > 0;
    }

    private int nextId() {
        Integer id = jdbcTemplate.queryForObject("SELECT COALESCE(MAX(PatientID), 0) + 1 FROM Patients", Integer.class);
        return id == null ? 1 : id;
    }

    private PatientDto mapRow(ResultSet rs) throws SQLException {
        PatientDto dto = new PatientDto();
        dto.setPatientId(rs.getInt("PatientID"));
        dto.setFullName(rs.getString("FullName"));
        dto.setBirthDate(rs.getObject("BirthDate", LocalDate.class));
        dto.setAddress(rs.getString("Address"));
        dto.setPolyclinicId(rs.getInt("PolyclinicID"));
        dto.setOmsNumber(rs.getString("OMSNumber"));
        dto.setSnils(rs.getString("SNILS"));
        dto.setPassportData(rs.getString("PassportData"));
        dto.setPhoneNumber(rs.getString("PhoneNumber"));
        return dto;
    }
}

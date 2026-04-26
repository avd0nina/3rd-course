package ru.shift.mednet2.repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;
import ru.shift.mednet2.dto.OperationDto;

@Repository
public class OperationRepository {

    private final JdbcTemplate jdbcTemplate;

    public OperationRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<OperationDto> findAll() {
        String sql = """
                SELECT OperationID, PatientID, DoctorID, TypeID, PlannedDate, PerformedDate, Outcome, Description
                FROM Operations
                ORDER BY PerformedDate DESC
                """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> mapRow(rs));
    }

    public Optional<OperationDto> findById(int id) {
        String sql = """
                SELECT OperationID, PatientID, DoctorID, TypeID, PlannedDate, PerformedDate, Outcome, Description
                FROM Operations
                WHERE OperationID = ?
                """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> mapRow(rs), id).stream().findFirst();
    }

    public List<OperationDto> findByPatientId(int patientId) {
        String sql = """
                SELECT OperationID, PatientID, DoctorID, TypeID, PlannedDate, PerformedDate, Outcome, Description
                FROM Operations
                WHERE PatientID = ?
                ORDER BY PerformedDate DESC
                """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> mapRow(rs), patientId);
    }

    public OperationDto create(OperationDto dto) {
        int id = nextId();
        String sql = """
                INSERT INTO Operations (OperationID, PatientID, DoctorID, TypeID, PlannedDate, PerformedDate, Outcome, Description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """;
        jdbcTemplate.update(
                sql,
                id,
                dto.getPatientId(),
                dto.getDoctorId(),
                dto.getTypeId(),
                dto.getPlannedDate(),
                dto.getPerformedDate(),
                dto.getOutcome(),
                dto.getDescription()
        );
        dto.setOperationId(id);
        return dto;
    }

    public boolean update(OperationDto dto) {
        String sql = """
                UPDATE Operations
                SET PatientID = ?, DoctorID = ?, TypeID = ?, PlannedDate = ?, PerformedDate = ?, Outcome = ?, Description = ?
                WHERE OperationID = ?
                """;
        return jdbcTemplate.update(
                sql,
                dto.getPatientId(),
                dto.getDoctorId(),
                dto.getTypeId(),
                dto.getPlannedDate(),
                dto.getPerformedDate(),
                dto.getOutcome(),
                dto.getDescription(),
                dto.getOperationId()
        ) > 0;
    }

    public boolean deleteById(int id) {
        String sql = "DELETE FROM Operations WHERE OperationID = ?";
        return jdbcTemplate.update(sql, id) > 0;
    }

    private int nextId() {
        Integer id = jdbcTemplate.queryForObject("SELECT COALESCE(MAX(OperationID), 0) + 1 FROM Operations", Integer.class);
        return id == null ? 1 : id;
    }

    private OperationDto mapRow(ResultSet rs) throws SQLException {
        OperationDto dto = new OperationDto();
        dto.setOperationId(rs.getInt("OperationID"));
        dto.setPatientId(rs.getInt("PatientID"));
        dto.setDoctorId(rs.getInt("DoctorID"));
        dto.setTypeId(rs.getInt("TypeID"));
        dto.setPlannedDate(rs.getObject("PlannedDate", LocalDate.class));
        dto.setPerformedDate(rs.getObject("PerformedDate", LocalDate.class));
        dto.setOutcome(rs.getString("Outcome"));
        dto.setDescription(rs.getString("Description"));
        return dto;
    }
}

package ru.shift.mednet2.repository;

import java.util.List;
import java.util.Optional;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;
import ru.shift.mednet2.dto.MedicalInstitutionDto;

@Repository
public class MedicalInstitutionRepository {

    private final JdbcTemplate jdbcTemplate;

    public MedicalInstitutionRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<MedicalInstitutionDto> findAll() {
        String sql = """
                SELECT InstitutionID, Name, Address, Type
                FROM MedicalInstitutions
                ORDER BY Name
                """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> mapRow(rs));
    }

    public Optional<MedicalInstitutionDto> findById(int id) {
        String sql = """
                SELECT InstitutionID, Name, Address, Type
                FROM MedicalInstitutions
                WHERE InstitutionID = ?
                """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> mapRow(rs), id).stream().findFirst();
    }

    public MedicalInstitutionDto create(MedicalInstitutionDto dto) {
        int id = nextId();
        String sql = """
                INSERT INTO MedicalInstitutions (InstitutionID, Name, Address, Type)
                VALUES (?, ?, ?, ?)
                """;
        jdbcTemplate.update(sql, id, dto.getName(), dto.getAddress(), dto.getType());
        dto.setInstitutionId(id);
        return dto;
    }

    public boolean update(MedicalInstitutionDto dto) {
        String sql = """
                UPDATE MedicalInstitutions
                SET Name = ?, Address = ?, Type = ?
                WHERE InstitutionID = ?
                """;
        return jdbcTemplate.update(sql, dto.getName(), dto.getAddress(), dto.getType(), dto.getInstitutionId()) > 0;
    }

    public boolean deleteById(int id) {
        String sql = "DELETE FROM MedicalInstitutions WHERE InstitutionID = ?";
        return jdbcTemplate.update(sql, id) > 0;
    }

    private int nextId() {
        Integer id = jdbcTemplate.queryForObject(
                "SELECT COALESCE(MAX(InstitutionID), 0) + 1 FROM MedicalInstitutions",
                Integer.class
        );
        return id == null ? 1 : id;
    }

    private MedicalInstitutionDto mapRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        MedicalInstitutionDto dto = new MedicalInstitutionDto();
        dto.setInstitutionId(rs.getInt("InstitutionID"));
        dto.setName(rs.getString("Name"));
        dto.setAddress(rs.getString("Address"));
        dto.setType(rs.getString("Type"));
        return dto;
    }
}

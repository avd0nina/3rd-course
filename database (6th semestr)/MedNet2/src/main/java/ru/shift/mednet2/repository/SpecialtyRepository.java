package ru.shift.mednet2.repository;

import java.util.List;
import java.util.Optional;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;
import ru.shift.mednet2.dto.SpecialtyDto;

@Repository
public class SpecialtyRepository {

    private final JdbcTemplate jdbcTemplate;

    public SpecialtyRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<SpecialtyDto> findAll() {
        String sql = """
                SELECT SpecialtyID, Name, VacationDays, BaseSalary, HazardCoefficient
                FROM Specialties
                ORDER BY Name
                """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> mapRow(rs));
    }

    public Optional<SpecialtyDto> findById(int id) {
        String sql = """
                SELECT SpecialtyID, Name, VacationDays, BaseSalary, HazardCoefficient
                FROM Specialties
                WHERE SpecialtyID = ?
                """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> mapRow(rs), id).stream().findFirst();
    }

    public SpecialtyDto create(SpecialtyDto dto) {
        int id = nextId();
        String sql = """
                INSERT INTO Specialties (SpecialtyID, Name, VacationDays, BaseSalary, HazardCoefficient)
                VALUES (?, ?, ?, ?, ?)
                """;
        jdbcTemplate.update(sql, id, dto.getName(), dto.getVacationDays(), dto.getBaseSalary(), dto.getHazardCoefficient());
        dto.setSpecialtyId(id);
        return dto;
    }

    public boolean update(SpecialtyDto dto) {
        String sql = """
                UPDATE Specialties
                SET Name = ?, VacationDays = ?, BaseSalary = ?, HazardCoefficient = ?
                WHERE SpecialtyID = ?
                """;
        return jdbcTemplate.update(
                sql,
                dto.getName(),
                dto.getVacationDays(),
                dto.getBaseSalary(),
                dto.getHazardCoefficient(),
                dto.getSpecialtyId()
        ) > 0;
    }

    public boolean deleteById(int id) {
        String sql = "DELETE FROM Specialties WHERE SpecialtyID = ?";
        return jdbcTemplate.update(sql, id) > 0;
    }

    private int nextId() {
        Integer id = jdbcTemplate.queryForObject("SELECT COALESCE(MAX(SpecialtyID), 0) + 1 FROM Specialties", Integer.class);
        return id == null ? 1 : id;
    }

    private SpecialtyDto mapRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        SpecialtyDto dto = new SpecialtyDto();
        dto.setSpecialtyId(rs.getInt("SpecialtyID"));
        dto.setName(rs.getString("Name"));
        dto.setVacationDays(rs.getInt("VacationDays"));
        dto.setBaseSalary(rs.getInt("BaseSalary"));
        dto.setHazardCoefficient(rs.getDouble("HazardCoefficient"));
        return dto;
    }
}

package ru.shift.mednet2.repository;

import java.util.List;
import java.util.Optional;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;
import ru.shift.mednet2.dto.EmployeeDto;

@Repository
public class EmployeeRepository {

    private final JdbcTemplate jdbcTemplate;

    public EmployeeRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<EmployeeDto> findAll() {
        String sql = """
                SELECT EmployeeID, FullName
                FROM Employees
                ORDER BY FullName
                """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> mapRow(rs));
    }

    public Optional<EmployeeDto> findById(int id) {
        String sql = """
                SELECT EmployeeID, FullName
                FROM Employees
                WHERE EmployeeID = ?
                """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> mapRow(rs), id).stream().findFirst();
    }

    public EmployeeDto create(EmployeeDto dto) {
        int id = nextId();
        String sql = """
                INSERT INTO Employees (EmployeeID, FullName)
                VALUES (?, ?)
                """;
        jdbcTemplate.update(sql, id, dto.getFullName());
        dto.setEmployeeId(id);
        return dto;
    }

    public boolean update(EmployeeDto dto) {
        String sql = """
                UPDATE Employees
                SET FullName = ?
                WHERE EmployeeID = ?
                """;
        return jdbcTemplate.update(sql, dto.getFullName(), dto.getEmployeeId()) > 0;
    }

    public boolean deleteById(int id) {
        String sql = "DELETE FROM Employees WHERE EmployeeID = ?";
        return jdbcTemplate.update(sql, id) > 0;
    }

    private int nextId() {
        Integer id = jdbcTemplate.queryForObject("SELECT COALESCE(MAX(EmployeeID), 0) + 1 FROM Employees", Integer.class);
        return id == null ? 1 : id;
    }

    private EmployeeDto mapRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        EmployeeDto dto = new EmployeeDto();
        dto.setEmployeeId(rs.getInt("EmployeeID"));
        dto.setFullName(rs.getString("FullName"));
        return dto;
    }
}

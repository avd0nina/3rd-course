package ru.shift.mednet2.service;

import java.util.List;
import java.util.NoSuchElementException;
import org.springframework.stereotype.Service;
import ru.shift.mednet2.dto.EmployeeDto;
import ru.shift.mednet2.repository.EmployeeRepository;

@Service
public class EmployeeService {

    private final EmployeeRepository repository;

    public EmployeeService(EmployeeRepository repository) {
        this.repository = repository;
    }

    public List<EmployeeDto> getAll() {
        return repository.findAll();
    }

    public EmployeeDto getById(int id) {
        return repository.findById(id).orElseThrow(() -> new NoSuchElementException("Employee not found: " + id));
    }

    public EmployeeDto create(EmployeeDto dto) {
        dto.setFullName(dto.getFullName().trim());
        return repository.create(dto);
    }

    public EmployeeDto update(int id, EmployeeDto dto) {
        dto.setEmployeeId(id);
        dto.setFullName(dto.getFullName().trim());
        if (!repository.update(dto)) {
            throw new NoSuchElementException("Employee not found: " + id);
        }
        return dto;
    }

    public void delete(int id) {
        if (!repository.deleteById(id)) {
            throw new NoSuchElementException("Employee not found: " + id);
        }
    }
}

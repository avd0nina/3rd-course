package ru.shift.mednet2.service;

import java.time.LocalDate;
import java.util.List;
import java.util.NoSuchElementException;
import org.springframework.stereotype.Service;
import ru.shift.mednet2.dto.PatientDto;
import ru.shift.mednet2.repository.PatientRepository;

@Service
public class PatientService {

    private final PatientRepository repository;

    public PatientService(PatientRepository repository) {
        this.repository = repository;
    }

    public List<PatientDto> getAll(Integer polyclinicId) {
        if (polyclinicId == null) {
            return repository.findAll();
        }
        return repository.findByPolyclinicId(polyclinicId);
    }

    public PatientDto getById(int id) {
        return repository.findById(id).orElseThrow(() -> new NoSuchElementException("Patient not found: " + id));
    }

    public PatientDto create(PatientDto dto) {
        validateBirthDate(dto.getBirthDate());
        dto.setFullName(dto.getFullName().trim());
        dto.setAddress(dto.getAddress().trim());
        return repository.create(dto);
    }

    public PatientDto update(int id, PatientDto dto) {
        validateBirthDate(dto.getBirthDate());
        dto.setPatientId(id);
        dto.setFullName(dto.getFullName().trim());
        dto.setAddress(dto.getAddress().trim());
        if (!repository.update(dto)) {
            throw new NoSuchElementException("Patient not found: " + id);
        }
        return dto;
    }

    public void delete(int id) {
        if (!repository.deleteById(id)) {
            throw new NoSuchElementException("Patient not found: " + id);
        }
    }

    private void validateBirthDate(LocalDate birthDate) {
        if (birthDate.isAfter(LocalDate.now()) || birthDate.isEqual(LocalDate.now())) {
            throw new IllegalArgumentException("birthDate must be before today");
        }
    }
}

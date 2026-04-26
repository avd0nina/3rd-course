package ru.shift.mednet2.service;

import java.util.List;
import java.util.Locale;
import java.util.NoSuchElementException;
import org.springframework.stereotype.Service;
import ru.shift.mednet2.dto.MedicalInstitutionDto;
import ru.shift.mednet2.repository.MedicalInstitutionRepository;

@Service
public class MedicalInstitutionService {

    private final MedicalInstitutionRepository repository;

    public MedicalInstitutionService(MedicalInstitutionRepository repository) {
        this.repository = repository;
    }

    public List<MedicalInstitutionDto> getAll() {
        return repository.findAll();
    }

    public MedicalInstitutionDto getById(int id) {
        return repository.findById(id).orElseThrow(() -> new NoSuchElementException("Institution not found: " + id));
    }

    public MedicalInstitutionDto create(MedicalInstitutionDto dto) {
        dto.setType(normalizeType(dto.getType()));
        return repository.create(dto);
    }

    public MedicalInstitutionDto update(int id, MedicalInstitutionDto dto) {
        dto.setInstitutionId(id);
        dto.setType(normalizeType(dto.getType()));
        if (!repository.update(dto)) {
            throw new NoSuchElementException("Institution not found: " + id);
        }
        return dto;
    }

    public void delete(int id) {
        if (!repository.deleteById(id)) {
            throw new NoSuchElementException("Institution not found: " + id);
        }
    }

    private String normalizeType(String value) {
        String normalized = value.trim().toLowerCase(Locale.ROOT);
        return switch (normalized) {
            case "hospital" -> "Hospital";
            case "polyclinic" -> "Polyclinic";
            case "laboratory" -> "Laboratory";
            default -> throw new IllegalArgumentException("Unsupported institution type: " + value);
        };
    }
}

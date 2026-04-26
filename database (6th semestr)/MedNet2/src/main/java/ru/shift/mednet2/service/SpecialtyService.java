package ru.shift.mednet2.service;

import java.util.List;
import java.util.NoSuchElementException;
import org.springframework.stereotype.Service;
import ru.shift.mednet2.dto.SpecialtyDto;
import ru.shift.mednet2.repository.SpecialtyRepository;

@Service
public class SpecialtyService {

    private final SpecialtyRepository repository;

    public SpecialtyService(SpecialtyRepository repository) {
        this.repository = repository;
    }

    public List<SpecialtyDto> getAll() {
        return repository.findAll();
    }

    public SpecialtyDto getById(int id) {
        return repository.findById(id).orElseThrow(() -> new NoSuchElementException("Specialty not found: " + id));
    }

    public SpecialtyDto create(SpecialtyDto dto) {
        dto.setName(dto.getName().trim());
        return repository.create(dto);
    }

    public SpecialtyDto update(int id, SpecialtyDto dto) {
        dto.setSpecialtyId(id);
        dto.setName(dto.getName().trim());
        if (!repository.update(dto)) {
            throw new NoSuchElementException("Specialty not found: " + id);
        }
        return dto;
    }

    public void delete(int id) {
        if (!repository.deleteById(id)) {
            throw new NoSuchElementException("Specialty not found: " + id);
        }
    }
}

package ru.shift.mednet2.service;

import java.time.LocalDate;
import java.util.List;
import java.util.Locale;
import java.util.NoSuchElementException;
import org.springframework.stereotype.Service;
import ru.shift.mednet2.dto.OperationDto;
import ru.shift.mednet2.repository.OperationRepository;

@Service
public class OperationService {

    private final OperationRepository repository;

    public OperationService(OperationRepository repository) {
        this.repository = repository;
    }

    public List<OperationDto> getAll(Integer patientId) {
        if (patientId == null) {
            return repository.findAll();
        }
        return repository.findByPatientId(patientId);
    }

    public OperationDto getById(int id) {
        return repository.findById(id).orElseThrow(() -> new NoSuchElementException("Operation not found: " + id));
    }

    public OperationDto create(OperationDto dto) {
        validateDates(dto.getPlannedDate(), dto.getPerformedDate());
        dto.setOutcome(normalizeOutcome(dto.getOutcome()));
        return repository.create(dto);
    }

    public OperationDto update(int id, OperationDto dto) {
        validateDates(dto.getPlannedDate(), dto.getPerformedDate());
        dto.setOperationId(id);
        dto.setOutcome(normalizeOutcome(dto.getOutcome()));
        if (!repository.update(dto)) {
            throw new NoSuchElementException("Operation not found: " + id);
        }
        return dto;
    }

    public void delete(int id) {
        if (!repository.deleteById(id)) {
            throw new NoSuchElementException("Operation not found: " + id);
        }
    }

    private void validateDates(LocalDate plannedDate, LocalDate performedDate) {
        if (performedDate.isAfter(LocalDate.now())) {
            throw new IllegalArgumentException("performedDate must be less than or equal to today");
        }
        if (plannedDate != null && performedDate.isBefore(plannedDate)) {
            throw new IllegalArgumentException("performedDate must be greater than or equal to plannedDate");
        }
    }

    private String normalizeOutcome(String outcome) {
        String normalized = outcome.trim().toLowerCase(Locale.ROOT);
        return switch (normalized) {
            case "success", "fatal", "complications", "canceled" -> normalized;
            default -> throw new IllegalArgumentException("Unsupported operation outcome: " + outcome);
        };
    }
}

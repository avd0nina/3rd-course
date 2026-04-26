package ru.shift.mednet2.controller;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import ru.shift.mednet2.dto.OperationDto;
import ru.shift.mednet2.service.OperationService;

@RestController
@RequestMapping("/api/v1/operations")
@Validated
public class OperationController {

    private final OperationService service;

    public OperationController(OperationService service) {
        this.service = service;
    }

    @GetMapping
    public List<OperationDto> getAll(@RequestParam(required = false) @Min(1) Integer patientId) {
        return service.getAll(patientId);
    }

    @GetMapping("/{id}")
    public OperationDto getById(@PathVariable @Min(1) int id) {
        return service.getById(id);
    }

    @PostMapping
    public ResponseEntity<OperationDto> create(@Valid @RequestBody OperationDto dto) {
        return ResponseEntity.status(HttpStatus.CREATED).body(service.create(dto));
    }

    @PutMapping("/{id}")
    public OperationDto update(@PathVariable @Min(1) int id, @Valid @RequestBody OperationDto dto) {
        return service.update(id, dto);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable @Min(1) int id) {
        service.delete(id);
        return ResponseEntity.noContent().build();
    }
}

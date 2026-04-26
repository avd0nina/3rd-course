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
import org.springframework.web.bind.annotation.RestController;
import ru.shift.mednet2.dto.SpecialtyDto;
import ru.shift.mednet2.service.SpecialtyService;

@RestController
@RequestMapping("/api/v1/specialties")
@Validated
public class SpecialtyController {

    private final SpecialtyService service;

    public SpecialtyController(SpecialtyService service) {
        this.service = service;
    }

    @GetMapping
    public List<SpecialtyDto> getAll() {
        return service.getAll();
    }

    @GetMapping("/{id}")
    public SpecialtyDto getById(@PathVariable @Min(1) int id) {
        return service.getById(id);
    }

    @PostMapping
    public ResponseEntity<SpecialtyDto> create(@Valid @RequestBody SpecialtyDto dto) {
        return ResponseEntity.status(HttpStatus.CREATED).body(service.create(dto));
    }

    @PutMapping("/{id}")
    public SpecialtyDto update(@PathVariable @Min(1) int id, @Valid @RequestBody SpecialtyDto dto) {
        return service.update(id, dto);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable @Min(1) int id) {
        service.delete(id);
        return ResponseEntity.noContent().build();
    }
}

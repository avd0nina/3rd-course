package ru.shift.mednet2.controller;

import java.util.List;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
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
import ru.shift.mednet2.dto.catalog.EntityDetailsDto;
import ru.shift.mednet2.dto.catalog.TableMetaDto;
import ru.shift.mednet2.dto.catalog.TableRowsDto;
import ru.shift.mednet2.service.CatalogService;

@RestController
@RequestMapping("/api/v1/catalog")
@Validated
public class CatalogController {

    private final CatalogService catalogService;

    public CatalogController(CatalogService catalogService) {
        this.catalogService = catalogService;
    }

    @GetMapping("/tables")
    public List<TableMetaDto> getTables(Authentication authentication) {
        return catalogService.getTables(authentication);
    }

    @GetMapping("/tables/{tableKey}/rows")
    public TableRowsDto getRows(
            Authentication authentication,
            @PathVariable String tableKey,
            @RequestParam(required = false) String search,
            @RequestParam(required = false) String type
    ) {
        return catalogService.getRows(authentication, tableKey, search, type);
    }

    @PostMapping("/tables/{tableKey}/rows")
    public ResponseEntity<Void> createRow(
            Authentication authentication,
            @PathVariable String tableKey,
            @RequestBody Map<String, Object> payload
    ) {
        catalogService.createRow(authentication, tableKey, payload);
        return ResponseEntity.noContent().build();
    }

    @PutMapping("/tables/{tableKey}/rows/{rowId}")
    public ResponseEntity<Void> updateRow(
            Authentication authentication,
            @PathVariable String tableKey,
            @PathVariable long rowId,
            @RequestBody Map<String, Object> payload
    ) {
        catalogService.updateRow(authentication, tableKey, rowId, payload);
        return ResponseEntity.noContent().build();
    }

    @DeleteMapping("/tables/{tableKey}/rows/{rowId}")
    public ResponseEntity<Void> deleteRow(
            Authentication authentication,
            @PathVariable String tableKey,
            @PathVariable long rowId
    ) {
        catalogService.deleteRow(authentication, tableKey, rowId);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/details/medical-institutions/{institutionId}")
    public EntityDetailsDto getInstitutionDetails(
            Authentication authentication,
            @PathVariable int institutionId
    ) {
        return catalogService.getInstitutionDetails(authentication, institutionId);
    }

    @GetMapping("/details/employees/{employeeId}")
    public EntityDetailsDto getEmployeeDetails(
            Authentication authentication,
            @PathVariable int employeeId
    ) {
        return catalogService.getEmployeeDetails(authentication, employeeId);
    }

    @GetMapping("/details/patients/{patientId}")
    public EntityDetailsDto getPatientDetails(
            Authentication authentication,
            @PathVariable int patientId
    ) {
        return catalogService.getPatientDetails(authentication, patientId);
    }
}

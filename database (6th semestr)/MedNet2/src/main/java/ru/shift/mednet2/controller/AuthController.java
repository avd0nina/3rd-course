package ru.shift.mednet2.controller;

import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import ru.shift.mednet2.dto.catalog.AuthMeDto;
import ru.shift.mednet2.security.AppRole;
import ru.shift.mednet2.service.CatalogService;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final CatalogService catalogService;

    public AuthController(CatalogService catalogService) {
        this.catalogService = catalogService;
    }

    @GetMapping("/me")
    public AuthMeDto me(Authentication authentication) {
        AppRole role = catalogService.getRole(authentication);
        return new AuthMeDto(
                authentication.getName(),
                role.getCode(),
                role.getDisplayName()
        );
    }
}

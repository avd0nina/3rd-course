package ru.shift.mednet2.service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.Set;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.stream.Collectors;
import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import ru.shift.mednet2.dto.catalog.ColumnMetaDto;
import ru.shift.mednet2.dto.catalog.DetailSectionDto;
import ru.shift.mednet2.dto.catalog.EntityDetailsDto;
import ru.shift.mednet2.dto.catalog.TableMetaDto;
import ru.shift.mednet2.dto.catalog.TablePermissionDto;
import ru.shift.mednet2.dto.catalog.TableRowsDto;
import ru.shift.mednet2.security.AppRole;

@Service
public class CatalogService {

    private static final String DB_SCHEMA = "public";

    private static final List<TableDefinition> TABLES = List.of(
            new TableDefinition("medicalinstitutions", "medicalinstitutions", "institutionid", "Медицинские учреждения", List.of("name", "address", "type")),
            new TableDefinition("hospitals", "hospitals", "hospitalid", "Больницы", List.of()),
            new TableDefinition("buildings", "buildings", "buildingid", "Корпуса", List.of("name", "address")),
            new TableDefinition("departments", "departments", "departmentid", "Отделения", List.of("name", "specialization")),
            new TableDefinition("wards", "wards", "wardid", "Палаты", List.of("number")),
            new TableDefinition("beds", "beds", "bedid", "Места", List.of("number", "status")),
            new TableDefinition("polyclinics", "polyclinics", "polyclinicid", "Поликлиники", List.of()),
            new TableDefinition("offices", "offices", "officeid", "Кабинеты", List.of("number")),
            new TableDefinition("laboratories", "laboratories", "laboratoryid", "Лаборатории", List.of("profiles")),
            new TableDefinition("laboratorycontracts", "laboratorycontracts", "contractid", "Договоры лабораторий", List.of("contractnumber")),
            new TableDefinition("employees", "employees", "employeeid", "Сотрудники", List.of("fullname")),
            new TableDefinition("specialties", "specialties", "specialtyid", "Специальности", List.of("name")),
            new TableDefinition("supportstaff", "supportstaff", "staffid", "Обслуживающий персонал", List.of("specialty")),
            new TableDefinition("doctors", "doctors", "doctorid", "Врачи", List.of("degree", "title")),
            new TableDefinition("employment", "employment", "employmentid", "Трудоустройство сотрудников", List.of("employmenttype")),
            new TableDefinition("operationtypes", "operationtypes", "typeid", "Типы операций", List.of("name")),
            new TableDefinition("certificates", "certificates", "certificateid", "Сертификаты", List.of("qualificationlevel")),
            new TableDefinition("patients", "patients", "patientid", "Пациенты", List.of("fullname", "address", "omsnumber", "snils", "passportdata", "phonenumber")),
            new TableDefinition("operations", "operations", "operationid", "Операции", List.of("outcome", "description")),
            new TableDefinition("placementjournal", "placementjournal", "placementid", "Журнал размещений", List.of()),
            new TableDefinition("visitjournal", "visitjournal", "visitid", "Журнал обращений", List.of("complaints")),
            new TableDefinition("medicalservices", "medicalservices", "serviceid", "Медицинские услуги", List.of("servicetype", "results", "notes"))
    );

    private static final Map<String, String> COLUMN_TITLES = Map.ofEntries(
            Map.entry("institutionid", "ID учреждения"),
            Map.entry("name", "Название"),
            Map.entry("address", "Адрес"),
            Map.entry("type", "Тип"),
            Map.entry("hospitalid", "ID больницы"),
            Map.entry("buildingid", "ID корпуса"),
            Map.entry("departmentid", "ID отделения"),
            Map.entry("specialization", "Специализация"),
            Map.entry("wardid", "ID палаты"),
            Map.entry("bedid", "ID места"),
            Map.entry("number", "Номер"),
            Map.entry("status", "Статус"),
            Map.entry("polyclinicid", "ID поликлиники"),
            Map.entry("officeid", "ID кабинета"),
            Map.entry("laboratoryid", "ID лаборатории"),
            Map.entry("profiles", "Профиль лаборатории"),
            Map.entry("contractid", "ID договора"),
            Map.entry("contractnumber", "Номер договора"),
            Map.entry("startdate", "Дата начала"),
            Map.entry("enddate", "Дата окончания"),
            Map.entry("employeeid", "ID сотрудника"),
            Map.entry("fullname", "ФИО"),
            Map.entry("specialtyid", "ID специальности"),
            Map.entry("vacationdays", "Дни отпуска"),
            Map.entry("basesalary", "Базовая зарплата"),
            Map.entry("hazardcoefficient", "Коэффициент вредности"),
            Map.entry("staffid", "ID персонала"),
            Map.entry("specialty", "Специальность"),
            Map.entry("doctorid", "ID врача"),
            Map.entry("degree", "Степень"),
            Map.entry("title", "Звание"),
            Map.entry("employmentid", "ID трудоустройства"),
            Map.entry("employmenttype", "Тип трудоустройства"),
            Map.entry("experienceathiring", "Стаж на момент приема"),
            Map.entry("typeid", "ID типа операции"),
            Map.entry("certificateid", "ID сертификата"),
            Map.entry("issuedate", "Дата выдачи"),
            Map.entry("qualificationlevel", "Уровень квалификации"),
            Map.entry("expirydate", "Дата окончания"),
            Map.entry("patientid", "ID пациента"),
            Map.entry("birthdate", "Дата рождения"),
            Map.entry("omsnumber", "ОМС"),
            Map.entry("snils", "СНИЛС"),
            Map.entry("passportdata", "Паспортные данные"),
            Map.entry("phonenumber", "Телефон"),
            Map.entry("operationid", "ID операции"),
            Map.entry("planneddate", "Плановая дата"),
            Map.entry("performeddate", "Дата выполнения"),
            Map.entry("outcome", "Исход"),
            Map.entry("description", "Описание"),
            Map.entry("placementid", "ID размещения"),
            Map.entry("admissiondate", "Дата поступления"),
            Map.entry("dischargedate", "Дата выписки"),
            Map.entry("visitid", "ID обращения"),
            Map.entry("visitdate", "Дата обращения"),
            Map.entry("complaints", "Жалобы"),
            Map.entry("serviceid", "ID услуги"),
            Map.entry("servicetype", "Тип услуги"),
            Map.entry("servicedate", "Дата услуги"),
            Map.entry("results", "Результаты"),
            Map.entry("notes", "Примечания")
    );

    private static final Set<String> LAB_READ_TABLES = Set.of(
            "medicalinstitutions",
            "hospitals",
            "polyclinics",
            "laboratories",
            "buildings",
            "departments",
            "wards",
            "beds",
            "offices",
            "laboratorycontracts",
            "employees",
            "doctors",
            "supportstaff",
            "specialties",
            "employment",
            "medicalservices"
    );

    private static final Set<String> LAB_MUTATE_TABLES = Set.of(
            "laboratories",
            "laboratorycontracts",
            "medicalservices"
    );

    private static final Set<String> LAB_CREATE_TABLES = Set.of(
            "laboratorycontracts",
            "medicalservices"
    );

    private final JdbcTemplate jdbcTemplate;

    public CatalogService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<TableMetaDto> getTables(Authentication authentication) {
        AppRole role = AppRole.fromAuthentication(authentication);
        Set<String> existingTableNames = loadExistingTableNames();
        List<TableMetaDto> result = new ArrayList<>();

        for (TableDefinition definition : TABLES) {
            if (!existingTableNames.contains(definition.tableName())) {
                continue;
            }
            TablePermissionDto permissions = permissionFor(role, definition.key());
            if (!permissions.canRead()) {
                continue;
            }
            result.add(new TableMetaDto(
                    definition.key(),
                    definition.tableName(),
                    definition.title(),
                    definition.idColumn(),
                    permissions
            ));
        }

        return result;
    }

    public TableRowsDto getRows(
            Authentication authentication,
            String tableKey,
            String search,
            String type
    ) {
        AppRole role = AppRole.fromAuthentication(authentication);
        TableDefinition definition = findTableDefinition(tableKey);
        TablePermissionDto permission = permissionFor(role, definition.key());
        assertReadable(permission, definition.title());

        List<String> columnKeys = loadColumnKeys(definition.tableName());
        List<ColumnMetaDto> columns = columnKeys
                .stream()
                .map(column -> new ColumnMetaDto(column, columnTitle(column)))
                .toList();

        StringBuilder sql = new StringBuilder("SELECT * FROM ").append(qualifiedTable(definition.tableName()));
        List<Object> args = new ArrayList<>();
        List<String> predicates = new ArrayList<>();

        String normalizedSearch = search == null ? "" : search.trim();
        if (!normalizedSearch.isBlank()) {
            List<String> searchColumns = definition.searchColumns();
            if (!searchColumns.isEmpty()) {
                String likeValue = "%" + normalizedSearch.toLowerCase(Locale.ROOT) + "%";
                String joined = searchColumns.stream()
                        .filter(columnKeys::contains)
                        .map(column -> {
                            args.add(likeValue);
                            return "LOWER(CAST(" + column + " AS TEXT)) LIKE ?";
                        })
                        .collect(Collectors.joining(" OR "));
                if (!joined.isBlank()) {
                    predicates.add("(" + joined + ")");
                }
            }
        }

        if ("medicalinstitutions".equals(definition.key()) && type != null && !type.isBlank()) {
            predicates.add("type = ?");
            args.add(normalizeInstitutionType(type));
        }

        if (!predicates.isEmpty()) {
            sql.append(" WHERE ").append(String.join(" AND ", predicates));
        }

        if (columnKeys.contains(definition.idColumn())) {
            sql.append(" ORDER BY ").append(definition.idColumn());
        }

        List<Map<String, Object>> rows = jdbcTemplate.queryForList(sql.toString(), args.toArray());
        return new TableRowsDto(columns, rows, permission);
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void createRow(
            Authentication authentication,
            String tableKey,
            Map<String, Object> payload
    ) {
        AppRole role = AppRole.fromAuthentication(authentication);
        TableDefinition definition = findTableDefinition(tableKey);
        TablePermissionDto permission = permissionFor(role, definition.key());
        if (!permission.canCreate()) {
            throw new AccessDeniedException("Недостаточно прав на создание записи в таблице \"" + definition.title() + "\"");
        }

        if (payload == null || payload.isEmpty()) {
            throw new IllegalArgumentException("Не переданы поля для создания");
        }

        Set<String> allowedColumns = Set.copyOf(loadColumnKeys(definition.tableName()));
        Map<String, String> columnTypes = loadColumnTypes(definition.tableName());
        Map<String, Object> normalizedPayload = new LinkedHashMap<>();
        payload.forEach((key, value) -> normalizedPayload.put(key.toLowerCase(Locale.ROOT), value));

        List<String> columns = new ArrayList<>();
        List<Object> args = new ArrayList<>();
        for (Map.Entry<String, Object> entry : normalizedPayload.entrySet()) {
            String column = entry.getKey();
            if (!allowedColumns.contains(column)) {
                continue;
            }
            Object value = coerceInputValue(columnTypes.get(column), entry.getValue(), column);
            if (value == null) {
                continue;
            }
            columns.add(column);
            args.add(value);
        }

        if (columns.isEmpty()) {
            throw new IllegalArgumentException("Нет допустимых полей для создания");
        }

        String sql = "INSERT INTO " + qualifiedTable(definition.tableName())
                + " (" + String.join(", ", columns) + ")"
                + " VALUES (" + columns.stream().map(column -> "?").collect(Collectors.joining(", ")) + ")";
        jdbcTemplate.update(sql, args.toArray());
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void updateRow(
            Authentication authentication,
            String tableKey,
            long rowId,
            Map<String, Object> payload
    ) {
        AppRole role = AppRole.fromAuthentication(authentication);
        TableDefinition definition = findTableDefinition(tableKey);
        TablePermissionDto permission = permissionFor(role, definition.key());
        if (!permission.canUpdate()) {
            throw new AccessDeniedException("Недостаточно прав на редактирование таблицы \"" + definition.title() + "\"");
        }

        if (payload == null || payload.isEmpty()) {
            throw new IllegalArgumentException("Не переданы поля для обновления");
        }

        Set<String> allowedColumns = loadColumnKeys(definition.tableName())
                .stream()
                .filter(column -> !column.equals(definition.idColumn()))
                .collect(Collectors.toSet());
        Map<String, String> columnTypes = loadColumnTypes(definition.tableName());

        List<String> updates = new ArrayList<>();
        List<Object> args = new ArrayList<>();

        Map<String, Object> normalizedPayload = new LinkedHashMap<>();
        payload.forEach((key, value) -> normalizedPayload.put(key.toLowerCase(Locale.ROOT), value));

        for (Map.Entry<String, Object> entry : normalizedPayload.entrySet()) {
            String column = entry.getKey();
            if (!allowedColumns.contains(column)) {
                continue;
            }
            Object value = coerceInputValue(columnTypes.get(column), entry.getValue(), column);
            updates.add(column + " = ?");
            args.add(value);
        }

        if (updates.isEmpty()) {
            throw new IllegalArgumentException("Нет допустимых полей для обновления");
        }

        args.add(rowId);
        String sql = "UPDATE " + qualifiedTable(definition.tableName())
                + " SET " + String.join(", ", updates)
                + " WHERE " + definition.idColumn() + " = ?";
        int updated = jdbcTemplate.update(sql, args.toArray());
        if (updated == 0) {
            throw new NoSuchElementException("Запись не найдена: " + rowId);
        }
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void deleteRow(Authentication authentication, String tableKey, long rowId) {
        AppRole role = AppRole.fromAuthentication(authentication);
        TableDefinition definition = findTableDefinition(tableKey);
        TablePermissionDto permission = permissionFor(role, definition.key());
        if (!permission.canDelete()) {
            throw new AccessDeniedException("Недостаточно прав на удаление таблицы \"" + definition.title() + "\"");
        }

        String sql = "DELETE FROM " + qualifiedTable(definition.tableName()) + " WHERE " + definition.idColumn() + " = ?";
        int deleted = jdbcTemplate.update(sql, rowId);
        if (deleted == 0) {
            throw new NoSuchElementException("Запись не найдена: " + rowId);
        }
    }

    public EntityDetailsDto getInstitutionDetails(Authentication authentication, int institutionId) {
        AppRole role = AppRole.fromAuthentication(authentication);
        assertReadable(permissionFor(role, "medicalinstitutions"), "Медицинские учреждения");

        Map<String, Object> institution = findById("medicalinstitutions", "institutionid", institutionId);
        List<DetailSectionDto> sections = new ArrayList<>();
        sections.add(section("medicalinstitutions", List.of(institution)));

        String type = String.valueOf(institution.getOrDefault("type", ""));
        if ("Hospital".equalsIgnoreCase(type)) {
            addSectionIfReadable(role, sections, "buildings", "SELECT * FROM buildings WHERE hospitalid = ? ORDER BY buildingid", institutionId);
            addSectionIfReadable(role, sections, "departments", "SELECT * FROM departments WHERE hospitalid = ? ORDER BY departmentid", institutionId);
            addSectionIfReadable(role, sections, "wards",
                    "SELECT w.* FROM wards w JOIN departments d ON d.departmentid = w.departmentid WHERE d.hospitalid = ? ORDER BY w.wardid",
                    institutionId);
            addSectionIfReadable(role, sections, "beds",
                    "SELECT b.* FROM beds b JOIN wards w ON w.wardid = b.wardid JOIN departments d ON d.departmentid = w.departmentid WHERE d.hospitalid = ? ORDER BY b.bedid",
                    institutionId);
        } else if ("Laboratory".equalsIgnoreCase(type)) {
            addSectionIfReadable(role, sections, "laboratories", "SELECT * FROM laboratories WHERE laboratoryid = ?", institutionId);
            addSectionIfReadable(role, sections, "laboratorycontracts", "SELECT * FROM laboratorycontracts WHERE laboratoryid = ? ORDER BY contractid", institutionId);
        } else if ("Polyclinic".equalsIgnoreCase(type)) {
            addSectionIfReadable(role, sections, "offices", "SELECT * FROM offices WHERE polyclinicid = ? ORDER BY officeid", institutionId);
        }

        return new EntityDetailsDto("Детали медицинского учреждения", sections);
    }

    public EntityDetailsDto getEmployeeDetails(Authentication authentication, int employeeId) {
        AppRole role = AppRole.fromAuthentication(authentication);
        assertReadable(permissionFor(role, "employees"), "Сотрудники");

        Map<String, Object> employee = findById("employees", "employeeid", employeeId);
        List<DetailSectionDto> sections = new ArrayList<>();
        sections.add(section("employees", List.of(employee)));

        addSectionIfReadable(role, sections, "doctors",
                "SELECT d.*, s.name AS specialtyname, s.vacationdays, s.basesalary, s.hazardcoefficient " +
                        "FROM doctors d LEFT JOIN specialties s ON s.specialtyid = d.specialtyid WHERE d.doctorid = ?",
                employeeId);
        addSectionIfReadable(role, sections, "supportstaff", "SELECT * FROM supportstaff WHERE staffid = ?", employeeId);
        addSectionIfReadable(role, sections, "certificates",
                "SELECT c.*, ot.name AS operationtypename FROM certificates c " +
                        "LEFT JOIN operationtypes ot ON ot.typeid = c.typeid WHERE c.doctorid = ? ORDER BY c.certificateid",
                employeeId);
        addSectionIfReadable(role, sections, "employment", "SELECT * FROM employment WHERE employeeid = ? ORDER BY employmentid", employeeId);

        return new EntityDetailsDto("Детали сотрудника", sections);
    }

    public EntityDetailsDto getPatientDetails(Authentication authentication, int patientId) {
        AppRole role = AppRole.fromAuthentication(authentication);
        assertReadable(permissionFor(role, "patients"), "Пациенты");

        Map<String, Object> patient = findById("patients", "patientid", patientId);
        List<DetailSectionDto> sections = new ArrayList<>();
        sections.add(section("patients", List.of(patient)));

        addSectionIfReadable(role, sections, "operations", "SELECT * FROM operations WHERE patientid = ? ORDER BY operationid", patientId);
        addSectionIfReadable(role, sections, "placementjournal", "SELECT * FROM placementjournal WHERE patientid = ? ORDER BY placementid", patientId);
        addSectionIfReadable(role, sections, "visitjournal", "SELECT * FROM visitjournal WHERE patientid = ? ORDER BY visitid", patientId);
        addSectionIfReadable(role, sections, "medicalservices", "SELECT * FROM medicalservices WHERE patientid = ? ORDER BY serviceid", patientId);

        return new EntityDetailsDto("Детали пациента", sections);
    }

    public AppRole getRole(Authentication authentication) {
        return AppRole.fromAuthentication(authentication);
    }

    private void addSectionIfReadable(
            AppRole role,
            List<DetailSectionDto> sections,
            String tableKey,
            String sql,
            Object arg
    ) {
        if (!permissionFor(role, tableKey).canRead()) {
            return;
        }
        sections.add(section(tableKey, jdbcTemplate.queryForList(sql, arg)));
    }

    private void assertReadable(TablePermissionDto permission, String tableTitle) {
        if (!permission.canRead()) {
            throw new AccessDeniedException("Нет прав на просмотр таблицы \"" + tableTitle + "\"");
        }
    }

    private TablePermissionDto permissionFor(AppRole role, String tableKey) {
        if (role == AppRole.ADMIN_SYSTEM) {
            return new TablePermissionDto(true, true, true, true);
        }
        boolean read = LAB_READ_TABLES.contains(tableKey);
        boolean create = LAB_CREATE_TABLES.contains(tableKey);
        boolean mutate = LAB_MUTATE_TABLES.contains(tableKey);
        return new TablePermissionDto(read, create, mutate, mutate);
    }

    private Set<String> loadExistingTableNames() {
        return Set.copyOf(jdbcTemplate.queryForList("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                """, String.class));
    }

    private List<String> loadColumnKeys(String tableName) {
        return jdbcTemplate.queryForList("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = ?
                ORDER BY ordinal_position
                """, String.class, tableName);
    }

    private Map<String, String> loadColumnTypes(String tableName) {
        return jdbcTemplate.query("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = ?
                """,
                rs -> {
                    Map<String, String> result = new LinkedHashMap<>();
                    while (rs.next()) {
                        result.put(rs.getString("column_name"), rs.getString("data_type"));
                    }
                    return result;
                },
                tableName
        );
    }

    private TableDefinition findTableDefinition(String tableKey) {
        return TABLES.stream()
                .filter(definition -> definition.key().equalsIgnoreCase(tableKey))
                .findFirst()
                .orElseThrow(() -> new NoSuchElementException("Неизвестная таблица: " + tableKey));
    }

    private String columnTitle(String key) {
        return COLUMN_TITLES.getOrDefault(key, key);
    }

    private String tableTitle(String tableKey) {
        return findTableDefinition(tableKey).title();
    }

    private DetailSectionDto section(String tableKey, List<Map<String, Object>> rows) {
        return new DetailSectionDto(tableKey, tableTitle(tableKey), rows);
    }

    private Map<String, Object> findById(String tableName, String idColumn, int idValue) {
        try {
            return jdbcTemplate.queryForMap(
                    "SELECT * FROM " + qualifiedTable(tableName) + " WHERE " + idColumn + " = ?",
                    idValue
            );
        } catch (EmptyResultDataAccessException ex) {
            throw new NoSuchElementException("Запись не найдена: " + idValue);
        }
    }

    private String qualifiedTable(String tableName) {
        return DB_SCHEMA + "." + tableName;
    }

    private String normalizeInstitutionType(String value) {
        String normalized = value.trim().toLowerCase(Locale.ROOT);
        return switch (normalized) {
            case "hospital", "больница" -> "Hospital";
            case "polyclinic", "поликлиника" -> "Polyclinic";
            case "laboratory", "лаборатория" -> "Laboratory";
            default -> throw new IllegalArgumentException("Неизвестный тип учреждения: " + value);
        };
    }

    private Object coerceInputValue(String dataType, Object value, String column) {
        if (!(value instanceof String text)) {
            return value;
        }

        String trimmed = text.trim();
        if (trimmed.isEmpty()) {
            return null;
        }
        if (dataType == null) {
            return trimmed;
        }

        try {
            return switch (dataType.toLowerCase(Locale.ROOT)) {
                case "smallint", "integer" -> Integer.valueOf(trimmed);
                case "bigint" -> Long.valueOf(trimmed);
                case "real", "double precision" -> Double.valueOf(trimmed);
                case "numeric", "decimal" -> new java.math.BigDecimal(trimmed);
                case "date" -> LocalDate.parse(trimmed);
                case "timestamp without time zone" -> LocalDateTime.parse(trimmed);
                case "boolean" -> parseBoolean(trimmed, column);
                default -> trimmed;
            };
        } catch (RuntimeException ex) {
            throw new IllegalArgumentException("Некорректное значение для поля \"" + column + "\": " + trimmed);
        }
    }

    private Boolean parseBoolean(String value, String column) {
        String normalized = value.toLowerCase(Locale.ROOT);
        return switch (normalized) {
            case "true", "1", "yes", "y", "да" -> true;
            case "false", "0", "no", "n", "нет" -> false;
            default -> throw new IllegalArgumentException("Некорректное булево значение для поля \"" + column + "\": " + value);
        };
    }

    private record TableDefinition(
            String key,
            String tableName,
            String idColumn,
            String title,
            List<String> searchColumns
    ) {
    }
}

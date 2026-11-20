package com.urbanwater.controller;

import com.urbanwater.model.WaterConsumption;
import com.urbanwater.service.WaterConsumptionService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/water/records")
public class WaterConsumptionController {

    private final WaterConsumptionService service;

    public WaterConsumptionController(WaterConsumptionService service) {
        this.service = service;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public WaterConsumption create(@Valid @RequestBody WaterConsumption record) {
        return service.create(record);
    }

    @GetMapping
    public List<WaterConsumption> findAll() {
        return service.findAll();
    }

    @GetMapping("/{id}")
    public WaterConsumption findById(@PathVariable Long id) {
        return service.findById(id);
    }

    @PutMapping("/{id}")
    public WaterConsumption update(
            @PathVariable Long id,
            @Valid @RequestBody WaterConsumption record
    ) {
        return service.update(id, record);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        service.delete(id);
    }
}
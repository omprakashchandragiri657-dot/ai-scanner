package tools;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.List;

/**
 * Batch importer for legacy job records.
 */
public class ImportJobs {

    private static final String INSERT_SQL =
        "INSERT INTO jobs (title, owner_id, status) VALUES (?, ?, ?)";

    private final Connection connection;

    public ImportJobs(Connection connection) {
        this.connection = connection;
    }

    public int importRows(List<JobRow> rows) throws SQLException {
        int inserted = 0;
        try (PreparedStatement statement = connection.prepareStatement(INSERT_SQL)) {
            for (JobRow row : rows) {
                statement.setString(1, row.title());
                statement.setLong(2, row.ownerId());
                statement.setString(3, row.status());
                statement.executeUpdate();
                inserted += 1;
            }
        }
        return inserted;
    }

    public record JobRow(String title, long ownerId, String status) {}
}
